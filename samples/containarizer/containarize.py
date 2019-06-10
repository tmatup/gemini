import json
import sys
import os
import shutil
import docker

def getFileContent(fileName):
    file = open(fileName, "r")
    content = file.read()
    file.close()
    return content

def getJSONContent(file):
    content = getFileContent(file)
    data = json.loads(content)

    return data

def containerize(docker_file_path, image_name, image_version):
    image_tag = image_name + ":" + image_version
    image_tag = image_tag.lower()

    try:
        client = docker.from_env()
        docker_client = docker.APIClient()

        generator = docker_client.build(path=docker_file_path, rm=True, tag=image_tag)
    except Exception as e:
        print(e)
        return False

    while True:
        try:
            output = generator.__next__()
            output = str(output, 'utf-8')
            output = output.replace("{", "");
            output = output.replace("}", "");
            output = output.replace("\\n", "");
            output = output.replace("\"stream\":", "")
            output = output.replace("\"", "")
            output = output.replace("---\\u003e", "")

            print(output)
        except StopIteration:
            print("Docker image build complete.")
            break
        except ValueError:
            print("Error parsing output from docker image build: %s" % output)
            return False
        except Exception as e:
            print(e)
            return False

    return True

def build(manifest_path):

    try:
        print("Processing manifest: " + manifest_path)

        manifest = getJSONContent(manifest_path)

    except Exception as e:
        print("Error loading build manifest: ", e)
        return

    # create model build folder
    print("Creating temporary build directory")

    currentPath = os.getcwd()

    path = currentPath.replace("\\", "/") + "/__model_build__"

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.mkdir(path)
    except Exception as e:
        print("Creation of the directory %s failed" % path, "\n", e)
        return

    # copying project data
    print("Copying application files")
    sourceDir = manifest["source"]
    try:
        shutil.copytree(sourceDir, path + "/app_source/")
    except OSError:
        print("Copy of source %s failed" % sourceDir, sys.exc_info()[0])
        return

    #generating microservice.py
    print("Generating microservice wrapper")
    print(manifest["entrypoint"]["module"])
    microserviceContent = getFileContent(currentPath + "/templates/microservice.py")
    microserviceContent = microserviceContent.replace("{app_module_name}", manifest["entrypoint"]["module"])
    microserviceContent = microserviceContent.replace("{init_function}", manifest["entrypoint"]["initFunction"])
    microserviceContent = microserviceContent.replace("{app_request_handler_function}", manifest["entrypoint"]["handleRequestFunction"])

    authFlag = "False"
    if manifest["auth"] == True:
        authFlag = "True"
    microserviceContent = microserviceContent.replace("{auth_enabled}", authFlag)

    try:
        f = open(path + "/app_source/microservice.py", "w")
        f.write(microserviceContent)
        f.close()
    except Exception as e:
        print("Error building microservice.py file from template", e)
        return
        
    print("Completed generating microservice.py")

    #generate docker file
    print("Building docker file")
    try:
        with open(currentPath + "/templates/docker_template.txt") as templateFile:
            dockerTemplate = templateFile.read()

        dockerTemplate = dockerTemplate.replace("{base_image}", manifest["baseImage"])
        #dockerTemplate = dockerTemplate.replace("{source_path}", path.replace("\\", "/") + "/app_source/")

        shutil.copy(manifest["requirements"], path + "/app_source/")

        dockerTemplate = dockerTemplate.replace("{requirements_file}", "requirements.txt")

        with open(path + "/dockerfile", 'w') as outfile:
            outfile.write(dockerTemplate)
    except Exception as e:
        print("Error building docker file", e)
        return

    print("Create docker container")
    model_name = manifest["name"]
    model_name = model_name.replace(" ", "_").lower()

    model_version = manifest["version"]
    model_version = model_version.replace(" ", "_").lower()

    result = containerize(path, model_name, model_version)
    if result == True:
        print("Completed building container: " + model_name + ", version: " + model_version)
    else:
        print("Error building container: " + model_name + ", version: " + model_version)

    #cleanup
    print("Cleanup of temporary build directory")
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
    except Exception as e:
        print("Removal of the directory %s failed\n" % path, e)

    print("Done")


if len(sys.argv) != 2:
    print("Usage:\n\tbuild [manifest file path]")
else:
    manifest_path = sys.argv[1]
    build(manifest_path)



