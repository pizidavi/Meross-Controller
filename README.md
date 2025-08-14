# Meross-Controller

Control Meross devices based on SolarEdge production

## Getting started

### Install tools

This project use [Mise](https://github.com/jdx/mise) as tool version manager

```sh
mise install
```

or install [uv](https://docs.astral.sh/uv/) manually

### Install dependencies

```sh
uv sync
```

### Create env file

```sh
cp .env.sample .env
```

### Start

```sh
uv run main.py
```
