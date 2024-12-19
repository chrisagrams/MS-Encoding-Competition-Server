import docker

docker_client = docker.APIClient()

def check_and_pull_image(image_name: str):
    try:
        docker_client.inspect_image(image_name)
    except docker.errors.ImageNotFound:
        docker_client.pull(image_name)