using Docker.DotNet;
using Docker.DotNet.Models;
using ICSharpCode.SharpZipLib.GZip;
using ICSharpCode.SharpZipLib.Tar;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace kontainarizer
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length != 1)
            {
                Console.Out.WriteLine("Usage:\n\tbuild [manifest file path]");
            } else
            {
                Program.build(args[0]);  
            }
        }

        static void build(string document)
        {
            Console.Out.WriteLine("Processing manifest: " + document);
            dynamic manifest = JsonConvert.DeserializeObject(File.ReadAllText(document));

            Console.Out.WriteLine("Creating temporary build directory");
            string cwd = Directory.GetCurrentDirectory();
            string mbd = cwd + "\\__model_build__";
            if (Directory.Exists(mbd))
            {
                Directory.Delete(mbd, true);
            }
            Directory.CreateDirectory(mbd);

            Console.Out.WriteLine("Copying application files");
            Program.copy((string)manifest.source, mbd + "\\app_source\\");

            Console.Out.WriteLine("Generating microservice wrapper");
            string microservice = File.ReadAllText(cwd + "\\templates\\microservice.py");
            microservice = microservice.Replace("{app_module_name}", (string)manifest.entrypoint.module);
            microservice = microservice.Replace("{init_function}", (string)manifest.entrypoint.initFunction);
            microservice = microservice.Replace("{app_request_handler_function}", (string)manifest.entrypoint.handleRequestFunction);
            microservice = microservice.Replace("{auth_enabled}", (bool)manifest.auth ? "True" : "False");
            File.WriteAllText(mbd + "/app_source/microservice.py", microservice);
            Console.Out.WriteLine("Completed generating microservice.py");

            Console.Out.WriteLine("Building docker file");
            string template = File.ReadAllText(cwd + "\\templates\\docker_template.txt");
            template = template.Replace("{base_image}", (string)manifest.baseImage);
            string requirements = Path.GetFileName((string)manifest.requirements);
            template = template.Replace("{requirements_file}", requirements);
            File.Copy((string)manifest.requirements, mbd + "\\app_source\\" + requirements, true);
            File.WriteAllText(mbd + "\\Dockerfile", template);

            Console.Out.WriteLine("Create docker container");
            string model = ((string)manifest.name).Replace(" ", "_").ToLower();
            string version = ((string)manifest.version).Replace(" ", "_").ToLower();
            if (containerize(mbd, model, version))
            {
                Console.Out.WriteLine("Completed building container: " + model + ", version: " + version);
            }
            else
            {
                Console.Out.WriteLine("Error building container: " + model + ", version: " + version);
            }

            Console.Out.WriteLine("Cleanup of temporary build directory");
            Directory.Delete(mbd, true);

            Console.Out.WriteLine("Done");
        }

        static void copy(string sourceDirectory, string targetDirectory)
        {
            DirectoryInfo diSource = new DirectoryInfo(sourceDirectory);
            DirectoryInfo diTarget = new DirectoryInfo(targetDirectory);

            copyall(diSource, diTarget);
        }
        public class Progress : IProgress<JSONMessage>
        {
            public void Report(JSONMessage value)
            {
                Console.Out.WriteLine(value.ToString());
            }
        }

        static bool containerize(string mbd, string image, string version)
        {
            DockerClient client = new DockerClientConfiguration(new Uri("npipe://./pipe/docker_engine")).CreateClient();

            /*// workable solution - using cmd
            // Start the child process.
            Process p = new Process();
            // Redirect the output stream of the child process.
            p.StartInfo.UseShellExecute = false;
            p.StartInfo.RedirectStandardOutput = true;
            p.StartInfo.FileName = "cmd.exe";
            p.StartInfo.Arguments = "/C docker build -t " + tag + " " + mbd;
            p.Start();
            // Read the output stream first and then wait.
            string output = p.StandardOutput.ReadToEnd();
            p.WaitForExit();*/

            string parent = Directory.GetParent(mbd).FullName;
            string tar = parent + "\\" + image + ".tar";
            Program.CreateTar(tar, mbd);
            using (var fs = new FileStream(tar, FileMode.Open))
            {
                string tag = (image + ":" + version).ToLower();
                var task = client.Images.BuildImageFromDockerfileAsync(
                    fs,
                    new ImageBuildParameters() { Dockerfile = "/__model_build__/Dockerfile", Tags = new List<string> { tag }, Remove = true, ForceRemove = true },
                    CancellationToken.None);
                using (var streamReader = new StreamReader(task.Result))
                {
                    string line;
                    while ((line = streamReader.ReadLine()) != null)
                    {
                        Console.Out.WriteLine(line);
                    }
                }
            }
            // client.Images.CreateImageAsync(new ImagesCreateParameters { Repo = mbd, Tag = tag }, null, new Progress()).Wait();
            /* var container = client.Containers.CreateContainerAsync(new CreateContainerParameters
            {
                WorkingDir = mbd,               
                ExposedPorts = new Dictionary<string, EmptyStruct> { { ExposedPort, new EmptyStruct() } },
                HostConfig = new HostConfig
                {
                    PortBindings = new Dictionary<string, IList<PortBinding>>
                    {
                        { ExposedPort, new List<PortBinding> { new PortBinding { HostIP = "localhost", HostPort = HostPort } } }
                    }
                }
            }).Result;

            return (container.ID != null);*/
            return true;
        }

        static void copyall(DirectoryInfo source, DirectoryInfo target)
        {
            Directory.CreateDirectory(target.FullName);

            // Copy each file into the new directory.
            foreach (FileInfo fi in source.GetFiles())
            {
                Console.WriteLine(@"Copying {0}\{1}", target.FullName, fi.Name);
                fi.CopyTo(Path.Combine(target.FullName, fi.Name), true);
            }

            // Copy each subdirectory using recursion.
            foreach (DirectoryInfo diSourceSubDir in source.GetDirectories())
            {
                DirectoryInfo nextTargetSubDir = target.CreateSubdirectory(diSourceSubDir.Name);
                copyall(diSourceSubDir, nextTargetSubDir);
            }
        }

        static void CreateTar(string outputTarFilename, string sourceDirectory)
        {
            using (FileStream fs = new FileStream(outputTarFilename, FileMode.Create, FileAccess.Write, FileShare.None))
            using (Stream gzipStream = new GZipOutputStream(fs))
            using (TarArchive tarArchive = TarArchive.CreateOutputTarArchive(gzipStream))
            {
                AddDirectoryFilesToTar(tarArchive, sourceDirectory, true);
            }
        }

        static void AddDirectoryFilesToTar(TarArchive tarArchive, string sourceDirectory, bool recurse)
        {
            // Recursively add sub-folders
            if (recurse)
            {
                string[] directories = Directory.GetDirectories(sourceDirectory);
                foreach (string directory in directories)
                    AddDirectoryFilesToTar(tarArchive, directory, recurse);
            }

            // Add files
            string[] filenames = Directory.GetFiles(sourceDirectory);
            foreach (string filename in filenames)
            {
                TarEntry tarEntry = TarEntry.CreateEntryFromFile(filename);
                tarArchive.WriteEntry(tarEntry, true);
            }
        }
    }
}
