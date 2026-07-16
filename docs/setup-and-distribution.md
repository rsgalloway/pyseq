# Setup and Distribution

This guide covers the environment configuration and source distribution options
that support more customized pyseq setups.

## Environment

PySeq reads configuration from standard environment variables. The repository
includes a `pyseq.env` example [envstack](https://github.com/rsgalloway/envstack)
file for users who want to manage those variables externally.

## Distribution

### Ubuntu 26.04 LTS

As of July 16, 2026, pyseq is packaged for Ubuntu 26.04 LTS (`resolute`) in
[`universe`](https://packages.ubuntu.com/resolute/python3-pyseq) as
`python3-pyseq`.

```bash
sudo apt install python3-pyseq
```

### Debian sid

As of July 16, 2026, pyseq is packaged in Debian unstable (`sid`) as
[`python3-pyseq`](https://packages.debian.org/sid/python/python3-pyseq).

```bash
sudo apt install python3-pyseq
```

### Source distribution

If installing from source you can use [distman](https://github.com/rsgalloway/distman)
to install PySeq using the provided `dist.json` file:

```bash
$ pip install -U distman
$ distman [-d]
```

Using distman will deploy the targets defined in the `dist.json` file to the
root folder defined by `${DEPLOY_ROOT}`.
