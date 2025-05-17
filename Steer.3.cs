using System;
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
                        byte[] buffer = new byte[4];
                        pipe.Read(buffer, 0, buffer.Length);
                        float tilt = BitConverter.ToSingle(buffer, 0);
                        steeringScale = -tilt;
                    }
                    catch
                    {
                    }
                    finally
                    {
                        if (pipe != null)
                            pipe.Dispose();
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
