using System;
using System.Globalization;
using System.Text;
using System.Threading.Tasks;
using GTA;

namespace Steer
{
    public class Steer : Script
    {
        float steeringScale = 0;
        System.IO.Pipes.NamedPipeServerStream pipe;

        public Steer()
        {
            Task.Run(() =>
            {
                while (true)
                {
                    try
                    {
                        pipe = new System.IO.Pipes.NamedPipeServerStream("tilt", System.IO.Pipes.PipeDirection.In);
                        pipe.WaitForConnection();
                        byte[] buffer = new byte[10];
                        pipe.Read(buffer, 0, buffer.Length);
                        var tilt = float.Parse(Encoding.UTF8.GetString(buffer), CultureInfo.InvariantCulture.NumberFormat);
                        steeringScale = -tilt;
                    }
                    catch
                    {
                    }
                    finally
                    {
                        pipe?.Dispose();
                    }
                }
            });

            Tick += OnTick;
            Aborted += OnAbort;
        }

        void OnTick(object sender, EventArgs e)
        {
            if (Game.Player.Character.CurrentVehicle != null)
                Game.Player.Character.CurrentVehicle.SteeringScale = steeringScale;
        }

        void OnAbort(object sender, EventArgs e)
        {
            Tick -= OnTick;
        }
    }
}
