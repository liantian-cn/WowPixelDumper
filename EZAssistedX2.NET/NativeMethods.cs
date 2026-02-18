using System.Runtime.InteropServices;
using System.Text;

namespace EZAssistedX2.NET;

internal static class NativeMethods
{
    public const uint WM_KEYDOWN = 0x0100;
    public const uint WM_KEYUP = 0x0101;
    public const int ERROR_ALREADY_EXISTS = 183;

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool PostMessageW(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("shell32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsUserAnAdmin();

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr CreateMutexW(IntPtr lpMutexAttributes, bool bInitialOwner, string lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ReleaseMutex(IntPtr hMutex);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(IntPtr hObject);

    /// <summary>
    /// 枚举所有标题包含指定文本的窗口，返回 (hwnd, title) 列表。
    /// </summary>
    public static List<(IntPtr Hwnd, string Title)> GetWindowsByTitle(string title)
    {
        var results = new List<(IntPtr, string)>();
        var sb = new StringBuilder(256);

        EnumWindows((hWnd, _) =>
        {
            sb.Clear();
            GetWindowText(hWnd, sb, sb.Capacity);
            var wt = sb.ToString();
            if (wt.Contains(title, StringComparison.OrdinalIgnoreCase))
            {
                results.Add((hWnd, wt));
            }
            return true;
        }, IntPtr.Zero);

        return results;
    }
}
