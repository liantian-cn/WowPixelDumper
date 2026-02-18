using Vortice.Direct3D;
using Vortice.Direct3D11;
using Vortice.DXGI;
using Vortice.Mathematics;

namespace EZAssistedX2.NET;

/// <summary>
/// 基于 DXGI Desktop Duplication API 的屏幕截图。
/// 每次调用 GrabFrame 获取一帧全屏像素数据 (BGRA)。
/// </summary>
internal sealed class ScreenCapture : IDisposable
{
    private readonly ID3D11Device _device;
    private readonly ID3D11DeviceContext _context;
    private readonly IDXGIOutputDuplication _duplication;
    private readonly int _width;
    private readonly int _height;
    private ID3D11Texture2D? _stagingTexture;
    private Format _stagingFormat;
    private bool _disposed;

    public int Width => _width;
    public int Height => _height;
    public string FormatName => _stagingFormat.ToString();

    public ScreenCapture(uint adapterIndex = 0, uint outputIndex = 0)
    {
        using var factory = DXGI.CreateDXGIFactory1<IDXGIFactory1>();
        factory.EnumAdapters1(adapterIndex, out var adapter).CheckError();
        using var _ = adapter;

        D3D11.D3D11CreateDevice(
            adapter,
            DriverType.Unknown,
            DeviceCreationFlags.BgraSupport,
            Array.Empty<FeatureLevel>(),
            out _device!,
            out _context!).CheckError();

        adapter.EnumOutputs(outputIndex, out var output).CheckError();
        using var _2 = output;

        var desc = output.Description;
        _width = desc.DesktopCoordinates.Right - desc.DesktopCoordinates.Left;
        _height = desc.DesktopCoordinates.Bottom - desc.DesktopCoordinates.Top;

        // 尝试 DuplicateOutput1（IDXGIOutput5），支持指定格式
        try
        {
            using var output5 = output.QueryInterface<IDXGIOutput5>();
            _duplication = output5.DuplicateOutput1(_device, new[] { Format.B8G8R8A8_UNorm });
        }
        catch
        {
            using var output1 = output.QueryInterface<IDXGIOutput1>();
            _duplication = output1.DuplicateOutput(_device);
        }

        // staging texture 将在首次 GrabFrame 时根据实际纹理格式创建
        _stagingFormat = Format.Unknown;
    }

    private ID3D11Texture2D CreateStagingTexture(Format format)
    {
        var texDesc = new Texture2DDescription
        {
            Width = (uint)_width,
            Height = (uint)_height,
            MipLevels = 1,
            ArraySize = 1,
            Format = format,
            SampleDescription = new SampleDescription(1, 0),
            Usage = ResourceUsage.Staging,
            CPUAccessFlags = CpuAccessFlags.Read,
        };
        return _device.CreateTexture2D(texDesc);
    }

    /// <summary>
    /// 截取全屏一帧，返回 BGRA 像素数据。失败返回 null。
    /// </summary>
    public byte[]? GrabFrame(uint timeoutMs = 500)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);

        IDXGIResource? resource = null;
        try
        {
            var result = _duplication.AcquireNextFrame(timeoutMs, out _, out resource);
            if (result.Failure || resource == null)
                return null;

            using var texture = resource.QueryInterface<ID3D11Texture2D>();

            // 检查获取到的纹理格式，如果与 staging 不匹配则重建
            var texDesc = texture.Description;
            if (_stagingTexture == null || texDesc.Format != _stagingFormat)
            {
                _stagingTexture?.Dispose();
                _stagingFormat = texDesc.Format;
                _stagingTexture = CreateStagingTexture(texDesc.Format);
            }

            _context.CopyResource(_stagingTexture, texture);

            var mapped = _context.Map(_stagingTexture, 0u, MapMode.Read, Vortice.Direct3D11.MapFlags.None);
            try
            {
                int rowPitch = (int)mapped.RowPitch;
                int bytesPerPixel = GetBytesPerPixel(texDesc.Format);
                var rawData = new byte[_width * _height * bytesPerPixel];

                unsafe
                {
                    byte* src = (byte*)mapped.DataPointer;
                    for (int y = 0; y < _height; y++)
                    {
                        var srcSpan = new ReadOnlySpan<byte>(src + y * rowPitch, _width * bytesPerPixel);
                        srcSpan.CopyTo(rawData.AsSpan(y * _width * bytesPerPixel));
                    }
                }

                // 如果格式已经是 BGRA8，直接返回
                if (texDesc.Format == Format.B8G8R8A8_UNorm)
                    return rawData;

                // 否则转换为 BGRA8
                return ConvertToBgra8(rawData, _width, _height, texDesc.Format);
            }
            finally
            {
                _context.Unmap(_stagingTexture, 0u);
            }
        }
        catch
        {
            return null;
        }
        finally
        {
            resource?.Dispose();
            try { _duplication.ReleaseFrame(); } catch { /* ignored */ }
        }
    }

    private static int GetBytesPerPixel(Format format) => format switch
    {
        Format.B8G8R8A8_UNorm => 4,
        Format.R8G8B8A8_UNorm => 4,
        Format.R10G10B10A2_UNorm => 4,
        Format.R16G16B16A16_Float => 8,
        _ => 4,
    };

    /// <summary>
    /// 将非 BGRA8 格式的像素数据转换为 BGRA8。
    /// </summary>
    private static byte[] ConvertToBgra8(byte[] rawData, int width, int height, Format format)
    {
        var pixels = new byte[width * height * 4];

        switch (format)
        {
            case Format.R8G8B8A8_UNorm:
                // RGBA → BGRA: 交换 R 和 B
                for (int i = 0; i < width * height; i++)
                {
                    int src = i * 4;
                    int dst = i * 4;
                    pixels[dst + 0] = rawData[src + 2]; // B
                    pixels[dst + 1] = rawData[src + 1]; // G
                    pixels[dst + 2] = rawData[src + 0]; // R
                    pixels[dst + 3] = rawData[src + 3]; // A
                }
                break;

            case Format.R16G16B16A16_Float:
                // 半精度浮点 → BGRA8
                for (int i = 0; i < width * height; i++)
                {
                    int src = i * 8;
                    int dst = i * 4;
                    float r = HalfToFloat(BitConverter.ToUInt16(rawData, src + 0));
                    float g = HalfToFloat(BitConverter.ToUInt16(rawData, src + 2));
                    float b = HalfToFloat(BitConverter.ToUInt16(rawData, src + 4));
                    pixels[dst + 0] = FloatToByte(b); // B
                    pixels[dst + 1] = FloatToByte(g); // G
                    pixels[dst + 2] = FloatToByte(r); // R
                    pixels[dst + 3] = 255;            // A
                }
                break;

            case Format.R10G10B10A2_UNorm:
                // 10-bit → BGRA8
                for (int i = 0; i < width * height; i++)
                {
                    int src = i * 4;
                    uint packed = BitConverter.ToUInt32(rawData, src);
                    byte r = (byte)((packed & 0x3FF) * 255 / 1023);
                    byte g = (byte)(((packed >> 10) & 0x3FF) * 255 / 1023);
                    byte b = (byte)(((packed >> 20) & 0x3FF) * 255 / 1023);
                    int dst = i * 4;
                    pixels[dst + 0] = b; // B
                    pixels[dst + 1] = g; // G
                    pixels[dst + 2] = r; // R
                    pixels[dst + 3] = 255; // A
                }
                break;

            default:
                // 未知格式，假设 BGRA8
                Buffer.BlockCopy(rawData, 0, pixels, 0, Math.Min(rawData.Length, pixels.Length));
                break;
        }

        return pixels;
    }

    private static float HalfToFloat(ushort half)
    {
        return (float)BitConverter.UInt16BitsToHalf(half);
    }

    private static byte FloatToByte(float value)
    {
        return (byte)Math.Clamp((int)(value * 255f + 0.5f), 0, 255);
    }

    /// <summary>
    /// 从全屏像素数据中提取指定区域的像素 (BGRA)。
    /// </summary>
    public static byte[] CropRegion(byte[] fullFrame, int frameWidth, int left, int top, int right, int bottom)
    {
        int regionW = right - left;
        int regionH = bottom - top;
        var cropped = new byte[regionW * regionH * 4];

        for (int y = 0; y < regionH; y++)
        {
            int srcOffset = ((top + y) * frameWidth + left) * 4;
            int dstOffset = y * regionW * 4;
            Buffer.BlockCopy(fullFrame, srcOffset, cropped, dstOffset, regionW * 4);
        }

        return cropped;
    }

    /// <summary>
    /// 获取像素数据中指定坐标的 (R, G, B) 值。数据格式为 BGRA。
    /// </summary>
    public static (byte R, byte G, byte B) GetPixel(byte[] data, int stride, int x, int y)
    {
        int offset = (y * stride + x) * 4;
        return (data[offset + 2], data[offset + 1], data[offset]);
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;

        _stagingTexture?.Dispose();
        _duplication.Dispose();
        _context.Dispose();
        _device.Dispose();
    }
}
