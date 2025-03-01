# Imagen API

[![Docker Pulls](https://img.shields.io/docker/pulls/arnocher/imagen-api)](https://hub.docker.com/r/arnocher/imagen-api)
[![GitHub issues](https://img.shields.io/github/issues/kressety/imagen-api)](https://github.com/kressety/imagen-api/issues)
[![GitHub stars](https://img.shields.io/github/stars/kressety/imagen-api)](https://github.com/kressety/imagen-api/stargazers)
[![GitHub license](https://img.shields.io/github/license/kressety/imagen-api)](https://github.com/kressety/imagen-api/blob/main/LICENSE)

## Overview

Imagen API is a project designed to provide an easy-to-use API for image processing. This project leverages the power of various cloud services to deliver efficient and scalable image processing capabilities.

## Getting Started

### Prerequisites

Make sure you have Docker installed on your machine. You will also need the following environment variables:

- `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID
- `CLOUDFLARE_API_TOKEN`: Your Cloudflare API Token
- `MODELSCOPE_API_TOKEN`: Your ModelScope API Token
- `DASHSCOPE_API_KEY`: Your Aliyun API Key

### Running with Docker

You can run the Imagen API using Docker with the following command:

```sh
docker run -d -p 5000:5000 \
    -e CLOUDFLARE_ACCOUNT_ID=your_cf_account_id \
    -e CLOUDFLARE_API_TOKEN=your_cf_api_token \
    -e MODELSCOPE_API_TOKEN=your_modelscope_api_token \
    -e DASHSCOPE_API_KEY=your_aliyun_api_key \
    arnocher/imagen-api
```

Replace the placeholder values with your actual API keys and tokens.

### Usage

Once the Docker container is running, the API will be accessible at `http://localhost:5000`. You can interact with the API using standard HTTP requests.

## Contributing

We welcome contributions to the Imagen API project. If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
