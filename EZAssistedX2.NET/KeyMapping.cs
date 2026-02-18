namespace EZAssistedX2.NET;

internal static class KeyMapping
{
    /// <summary>
    /// 颜色 (R, G, B) → 快捷键名称
    /// </summary>
    public static readonly Dictionary<(byte R, byte G, byte B), string> KeyColorMap = new()
    {
        [(13, 255, 0)] = "SHIFT-NUMPAD1",
        [(0, 255, 64)] = "SHIFT-NUMPAD2",
        [(0, 255, 140)] = "SHIFT-NUMPAD3",
        [(0, 255, 217)] = "SHIFT-NUMPAD4",
        [(0, 217, 255)] = "SHIFT-NUMPAD5",
        [(0, 140, 255)] = "SHIFT-NUMPAD6",
        [(0, 64, 255)] = "SHIFT-NUMPAD7",
        [(13, 0, 255)] = "SHIFT-NUMPAD8",
        [(89, 0, 255)] = "SHIFT-NUMPAD9",
        [(166, 0, 255)] = "SHIFT-NUMPAD0",
        [(242, 0, 255)] = "ALT-NUMPAD1",
        [(255, 0, 191)] = "ALT-NUMPAD2",
        [(255, 0, 115)] = "ALT-NUMPAD3",
        [(255, 0, 38)] = "ALT-NUMPAD4",
        [(255, 38, 0)] = "ALT-NUMPAD5",
        [(255, 115, 0)] = "ALT-NUMPAD6",
        [(255, 191, 0)] = "ALT-NUMPAD7",
        [(242, 255, 0)] = "ALT-NUMPAD8",
        [(166, 255, 0)] = "ALT-NUMPAD9",
        [(89, 255, 0)] = "ALT-NUMPAD0",
    };

    /// <summary>
    /// 键名 → 虚拟键码
    /// </summary>
    public static readonly Dictionary<string, int> VkDict = new()
    {
        ["SHIFT"] = 0x10,
        ["CTRL"] = 0x11,
        ["ALT"] = 0x12,
        ["NUMPAD0"] = 0x60,
        ["NUMPAD1"] = 0x61,
        ["NUMPAD2"] = 0x62,
        ["NUMPAD3"] = 0x63,
        ["NUMPAD4"] = 0x64,
        ["NUMPAD5"] = 0x65,
        ["NUMPAD6"] = 0x66,
        ["NUMPAD7"] = 0x67,
        ["NUMPAD8"] = 0x68,
        ["NUMPAD9"] = 0x69,
        ["F1"] = 0x70,
        ["F2"] = 0x71,
        ["F3"] = 0x72,
        ["F5"] = 0x74,
        ["F6"] = 0x75,
        ["F7"] = 0x76,
        ["F8"] = 0x77,
        ["F9"] = 0x78,
        ["F10"] = 0x79,
        ["F11"] = 0x7A,
    };

    /// <summary>
    /// 向目标窗口发送组合键，如 "CTRL-F1"。
    /// </summary>
    public static void SendHotKey(IntPtr hwnd, string hotKey)
    {
        var keys = hotKey.Split('-');

        // 按下所有键
        foreach (var k in keys)
        {
            if (VkDict.TryGetValue(k, out var vk))
                NativeMethods.PostMessageW(hwnd, NativeMethods.WM_KEYDOWN, (IntPtr)vk, IntPtr.Zero);
        }

        Thread.Sleep(5);

        // 反序释放所有键
        for (int i = keys.Length - 1; i >= 0; i--)
        {
            if (VkDict.TryGetValue(keys[i], out var vk))
                NativeMethods.PostMessageW(hwnd, NativeMethods.WM_KEYUP, (IntPtr)vk, IntPtr.Zero);
        }
    }
}
