import argparse
import ftplib
import logging as log
import os
import sys


def cli_argument_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server_ip',
                        help='FTP server IP.',
                        required=True,
                        type=str)
    parser.add_argument('-l', '--server_login',
                        type=str,
                        help='Login to the FTP server.',
                        required=True)
    parser.add_argument('-p', '--server_psw',
                        type=str,
                        help='Password to the FTP server.',
                        required=True)
    parser.add_argument('-i', '--image_path',
                        required=True,
                        type=str,
                        help='Path to container image on the FTP server.')
    parser.add_argument('-d', '--upload_dir',
                        required=True,
                        type=str,
                        help='Path to the directory on the target machine where to upload the container image.')
    parser.add_argument('-n', '--container_name',
                        required=True,
                        type=str,
                        help='Name of the docker container.')
    parser.add_argument('-mp', '--model_path',
                        required=True,
                        type=str,
                        help='Path to share directory with models to mount into docker container.')
    parser.add_argument('-dp', '--dataset_path',
                        required=True,
                        type=str,
                        help='Path to share directory with datasets to mount into docker container.')

    args = parser.parse_args()

    return args


def prepare_ftp_connection(server_ip, server_login, server_psw, image_path, log):
    log.info('Client script is connecting to the FTP server')
    ftp_connection = ftplib.FTP(server_ip, server_login, server_psw)
    log.info('FTP connection was created')

    image_dir = os.path.split(image_path)[0]
    if ftp_connection.pwd() != image_dir:
        log.info(f'Current directory {ftp_connection.pwd()} changed to target : {image_dir}')
        ftp_connection.cwd(image_dir)
    return ftp_connection


def upload_container_image(server_ip, server_login, server_psw, image_path, upload_dir, file_path, log):
    ftp_connection = prepare_ftp_connection(server_ip, server_login, server_psw, image_path, log)

    log.info('Client script is uploading image from server')
    with open(file_path, 'wb') as container_image:
        ftp_connection.retrbinary(f'RETR {os.path.split(image_path)[1]}', container_image.write)
    log.info('Upload completed')


def main():
    # Enable log formatting
    log.basicConfig(
        format='[ %(levelname)s ] %(message)s',
        level=log.INFO,
        stream=sys.stdout,
    )

    args = cli_argument_parser()

    image_name = os.path.split(args.image_path)[1]
    joined_pass = os.path.join(args.upload_dir, image_name)
    file_path = os.path.normpath(joined_pass)

    upload_container_image(
        args.server_ip,
        args.server_login,
        args.server_psw,
        args.image_path,
        args.upload_dir,
        file_path,
        log,
    )

    log.info('Docker is loading image from tar')
    os.system(f'docker load --input {file_path}')

    log.info('Docker run image')
    os.system(f'docker run --privileged -d -it '
              f'--name {args.container_name} '
              f'-v /dev:/dev '
              f'-v {args.model_path}:{args.model_path} '
              f'-v {args.dataset_path}:{args.dataset_path} '
              f'--network=host {image_name.split(".")[0]}')


if __name__ == '__main__':
    sys.exit(main() or 0)
