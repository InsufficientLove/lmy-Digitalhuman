using System.Diagnostics;

namespace LmyDigitalHuman.Services.Extensions
{
    /// <summary>
    /// 进程扩展方法
    /// </summary>
    public static class ProcessExtensions
    {
        public static Task WaitForExitAsync(this Process process)
        {
            var tcs = new TaskCompletionSource<bool>();
            process.EnableRaisingEvents = true;
            process.Exited += (sender, args) => tcs.TrySetResult(true);
            if (process.HasExited) tcs.TrySetResult(true);
            return tcs.Task;
        }

        public static async Task<bool> WaitForExitAsync(this Process process, TimeSpan timeout)
        {
            var tcs = new TaskCompletionSource<bool>();
            process.EnableRaisingEvents = true;
            process.Exited += (sender, args) => tcs.TrySetResult(true);
            if (process.HasExited)
            {
                tcs.TrySetResult(true);
                return true;
            }
            
            using var cts = new CancellationTokenSource(timeout);
            cts.Token.Register(() => tcs.TrySetResult(false));
            
            return await tcs.Task;
        }
    }
}