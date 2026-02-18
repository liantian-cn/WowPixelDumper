using System.Net;
using System.Text;
using System.Text.Json;

namespace Dumper.NET.Web;

public sealed class HttpApiServer : IDisposable
{
    private readonly HttpListener _listener = new();
    private readonly Func<Dictionary<string, object?>> _getPixelDump;
    private CancellationTokenSource? _cts;
    private Task? _serveTask;

    public HttpApiServer(Func<Dictionary<string, object?>> getPixelDump, string prefix = "http://127.0.0.1:65131/")
    {
        _getPixelDump = getPixelDump;
        _listener.Prefixes.Add(prefix);
    }

    public void Start()
    {
        if (_listener.IsListening)
        {
            return;
        }

        _cts = new CancellationTokenSource();
        _listener.Start();

        _serveTask = Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                HttpListenerContext? context = null;
                try
                {
                    context = await _listener.GetContextAsync();
                }
                catch (HttpListenerException)
                {
                    break;
                }
                catch (ObjectDisposedException)
                {
                    break;
                }

                if (context is null)
                {
                    continue;
                }

                _ = Task.Run(() => HandleRequest(context));
            }
        }, _cts.Token);
    }

    private void HandleRequest(HttpListenerContext context)
    {
        Dictionary<string, object?> data = _getPixelDump();
        string json = JsonSerializer.Serialize(data, new JsonSerializerOptions
        {
            WriteIndented = true,
        });

        byte[] bytes = Encoding.UTF8.GetBytes(json);

        context.Response.StatusCode = 200;
        context.Response.ContentType = "application/json; charset=utf-8";
        context.Response.Headers["Access-Control-Allow-Origin"] = "*";
        context.Response.Headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
        context.Response.Headers["Access-Control-Allow-Headers"] = "Content-Type";
        context.Response.ContentLength64 = bytes.Length;
        context.Response.OutputStream.Write(bytes, 0, bytes.Length);
        context.Response.OutputStream.Close();
    }

    public void Stop()
    {
        if (!_listener.IsListening)
        {
            return;
        }

        _cts?.Cancel();
        _listener.Stop();

        try
        {
            _serveTask?.Wait(1000);
        }
        catch
        {
            // ignore
        }

        _cts?.Dispose();
        _cts = null;
        _serveTask = null;
    }

    public void Dispose()
    {
        Stop();
        _listener.Close();
    }
}



