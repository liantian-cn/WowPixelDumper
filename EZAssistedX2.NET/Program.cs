using System.Runtime.InteropServices;

namespace EZAssistedX2.NET;

internal static class Program
{
    [STAThread]
    static void Main()
    {
        // Mutex 单实例检查
        var mutex = NativeMethods.CreateMutexW(IntPtr.Zero, false, "EZAssistedX2");
        bool alreadyRunning = Marshal.GetLastWin32Error() == NativeMethods.ERROR_ALREADY_EXISTS;

        ApplicationConfiguration.Initialize();

        if (alreadyRunning)
        {
            MessageBox.Show("程序已在运行中。", "EZAssistedX2", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        if (!NativeMethods.IsUserAnAdmin())
        {
            MessageBox.Show("必须以管理员身份运行。", "EZAssistedX2", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        try
        {
            Application.Run(new MainForm());
        }
        finally
        {
            NativeMethods.ReleaseMutex(mutex);
            NativeMethods.CloseHandle(mutex);
        }
    }
}
