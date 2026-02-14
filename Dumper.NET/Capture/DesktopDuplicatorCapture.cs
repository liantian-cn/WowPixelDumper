using System.Runtime.InteropServices;
using Dumper.NET.Core;
using Vortice.Direct3D;
using Vortice.Direct3D11;
using Vortice.DXGI;
using static Vortice.Direct3D11.D3D11;
using static Vortice.DXGI.DXGI;

namespace Dumper.NET.Capture;

public sealed record MonitorInfo(int AdapterIndex, int OutputIndex, string Description, bool IsPrimary, int Width, int Height)
{
    public override string ToString()
    {
        return $"Device[{AdapterIndex}] Output[{OutputIndex}]: Res:({Width}, {Height}) Primary:{IsPrimary} {Description}";
    }
}

public sealed class DesktopDuplicatorCapture : IDisposable
{
    private readonly IDXGIFactory1 _factory;
    private readonly IDXGIAdapter1 _adapter;
    private readonly IDXGIOutput _output;
    private readonly IDXGIOutput1 _output1;
    private IDXGIOutputDuplication _duplication;
    private readonly ID3D11Device _device;
    private readonly ID3D11DeviceContext _context;

    private ID3D11Texture2D? _stagingTexture;
    private Texture2DDescription _stagingDesc;

    public DesktopDuplicatorCapture(int adapterIndex, int outputIndex)
    {
        _factory = CreateDXGIFactory1<IDXGIFactory1>();

        if (_factory.EnumAdapters1((uint)adapterIndex, out _adapter).Failure)
        {
            throw new InvalidOperationException($"无法获取适配器: {adapterIndex}");
        }

        FeatureLevel[] levels =
        [
            FeatureLevel.Level_11_1,
            FeatureLevel.Level_11_0,
            FeatureLevel.Level_10_1,
            FeatureLevel.Level_10_0,
        ];

        var hr = D3D11CreateDevice(
            _adapter,
            DriverType.Unknown,
            DeviceCreationFlags.BgraSupport,
            levels,
            out _device,
            out _,
            out _context);

        if (hr.Failure)
        {
            throw new InvalidOperationException($"创建D3D11设备失败: {hr.Code}");
        }

        if (_adapter.EnumOutputs((uint)outputIndex, out _output).Failure)
        {
            throw new InvalidOperationException($"无法获取输出设备: {outputIndex}");
        }

        _output1 = _output.QueryInterface<IDXGIOutput1>();
        _duplication = CreateDuplication(_output1, _device);
    }

    public static List<MonitorInfo> EnumerateMonitors()
    {
        List<MonitorInfo> monitors = new();
        using IDXGIFactory1 factory = CreateDXGIFactory1<IDXGIFactory1>();

        uint adapterIndex = 0;
        while (factory.EnumAdapters1(adapterIndex, out IDXGIAdapter1? adapter).Success && adapter is not null)
        {
            uint outputIndex = 0;
            while (adapter.EnumOutputs(outputIndex, out IDXGIOutput? output).Success && output is not null)
            {
                OutputDescription desc = output.Description;
                int width = desc.DesktopCoordinates.Right - desc.DesktopCoordinates.Left;
                int height = desc.DesktopCoordinates.Bottom - desc.DesktopCoordinates.Top;
                bool isPrimary = desc.DesktopCoordinates.Left == 0 && desc.DesktopCoordinates.Top == 0;

                monitors.Add(new MonitorInfo(
                    (int)adapterIndex,
                    (int)outputIndex,
                    desc.DeviceName,
                    isPrimary,
                    width,
                    height));

                output.Dispose();
                outputIndex++;
            }

            adapter.Dispose();
            adapterIndex++;
        }

        return monitors;
    }

    public PixelFrame? GrabFrame(int timeoutMs = 100)
    {
        const int DxgiErrorWaitTimeout = unchecked((int)0x887A0027);
        var hr = _duplication.AcquireNextFrame((uint)timeoutMs, out OutduplFrameInfo _, out IDXGIResource? resource);
        if (hr.Code == DxgiErrorWaitTimeout)
        {
            return null;
        }

        if (hr.Failure || resource is null)
        {
            return null;
        }

        try
        {
            using ID3D11Texture2D gpuTexture = resource.QueryInterface<ID3D11Texture2D>();
            Texture2DDescription srcDesc = gpuTexture.Description;
            EnsureStagingTexture(srcDesc);

            _context.CopyResource(_stagingTexture!, gpuTexture);
            MappedSubresource mapped = _context.Map(_stagingTexture!, 0, MapMode.Read, Vortice.Direct3D11.MapFlags.None);

            try
            {
                byte[] bgra = ConvertToBgra(srcDesc, mapped);
                return new PixelFrame((int)srcDesc.Width, (int)srcDesc.Height, bgra);
            }
            finally
            {
                _context.Unmap(_stagingTexture!, 0);
            }
        }
        finally
        {
            resource.Dispose();
            _duplication.ReleaseFrame();
        }
    }

    private void EnsureStagingTexture(Texture2DDescription sourceDesc)
    {
        if (_stagingTexture is not null &&
            _stagingDesc.Width == sourceDesc.Width &&
            _stagingDesc.Height == sourceDesc.Height &&
            _stagingDesc.Format == sourceDesc.Format)
        {
            return;
        }

        _stagingTexture?.Dispose();

        _stagingDesc = new Texture2DDescription
        {
            Width = sourceDesc.Width,
            Height = sourceDesc.Height,
            MipLevels = 1,
            ArraySize = 1,
            Format = sourceDesc.Format,
            SampleDescription = new SampleDescription(1, 0),
            Usage = ResourceUsage.Staging,
            BindFlags = BindFlags.None,
            CPUAccessFlags = CpuAccessFlags.Read,
            MiscFlags = ResourceOptionFlags.None,
        };

        _stagingTexture = _device.CreateTexture2D(_stagingDesc);
    }

    private static IDXGIOutputDuplication CreateDuplication(IDXGIOutput1 output1, ID3D11Device device)
    {
        return output1.DuplicateOutput(device);
    }

    private static byte[] ConvertToBgra(Texture2DDescription desc, MappedSubresource mapped)
    {
        int width = (int)desc.Width;
        int height = (int)desc.Height;
        byte[] output = new byte[width * height * 4];

        for (int y = 0; y < height; y++)
        {
            IntPtr srcRow = IntPtr.Add(mapped.DataPointer, (int)(y * mapped.RowPitch));
            int dstRow = y * width * 4;

            switch (desc.Format)
            {
                case Format.B8G8R8A8_UNorm:
                    Marshal.Copy(srcRow, output, dstRow, width * 4);
                    break;

                case Format.R8G8B8A8_UNorm:
                    ConvertRgba8ToBgra(srcRow, output, dstRow, width);
                    break;

                case Format.R16G16B16A16_Float:
                    ConvertRgba16FloatToBgra8(srcRow, output, dstRow, width);
                    break;

                case Format.R10G10B10A2_UNorm:
                    ConvertR10G10B10A2ToBgra8(srcRow, output, dstRow, width);
                    break;

                default:
                    // 未支持格式时按BGRA尝试直拷，至少保证流程不断。
                    Marshal.Copy(srcRow, output, dstRow, width * 4);
                    break;
            }
        }

        return output;
    }

    private static unsafe void ConvertRgba8ToBgra(IntPtr srcRow, byte[] dst, int dstOffset, int width)
    {
        byte* src = (byte*)srcRow;
        int dstIndex = dstOffset;

        for (int x = 0; x < width; x++)
        {
            byte r = src[0];
            byte g = src[1];
            byte b = src[2];
            byte a = src[3];

            dst[dstIndex++] = b;
            dst[dstIndex++] = g;
            dst[dstIndex++] = r;
            dst[dstIndex++] = a;
            src += 4;
        }
    }

    private static unsafe void ConvertRgba16FloatToBgra8(IntPtr srcRow, byte[] dst, int dstOffset, int width)
    {
        ushort* src = (ushort*)srcRow;
        int dstIndex = dstOffset;

        for (int x = 0; x < width; x++)
        {
            float r = HalfToFloat(src[0]);
            float g = HalfToFloat(src[1]);
            float b = HalfToFloat(src[2]);
            float a = HalfToFloat(src[3]);

            dst[dstIndex++] = ToByte(b);
            dst[dstIndex++] = ToByte(g);
            dst[dstIndex++] = ToByte(r);
            dst[dstIndex++] = ToByte(a);
            src += 4;
        }
    }

    private static unsafe void ConvertR10G10B10A2ToBgra8(IntPtr srcRow, byte[] dst, int dstOffset, int width)
    {
        uint* src = (uint*)srcRow;
        int dstIndex = dstOffset;

        for (int x = 0; x < width; x++)
        {
            uint packed = src[x];
            uint r10 = packed & 0x3FF;
            uint g10 = (packed >> 10) & 0x3FF;
            uint b10 = (packed >> 20) & 0x3FF;
            uint a2 = (packed >> 30) & 0x3;

            dst[dstIndex++] = (byte)((b10 * 255) / 1023);
            dst[dstIndex++] = (byte)((g10 * 255) / 1023);
            dst[dstIndex++] = (byte)((r10 * 255) / 1023);
            dst[dstIndex++] = (byte)((a2 * 255) / 3);
        }
    }

    private static float HalfToFloat(ushort value)
    {
        return (float)BitConverter.UInt16BitsToHalf(value);
    }

    private static byte ToByte(float value)
    {
        float clamped = Math.Clamp(value, 0f, 1f);
        return (byte)(clamped * 255f + 0.5f);
    }

    public void Dispose()
    {
        _stagingTexture?.Dispose();
        _duplication.Dispose();
        _output1.Dispose();
        _output.Dispose();
        _context.Dispose();
        _device.Dispose();
        _adapter.Dispose();
        _factory.Dispose();
    }
}
