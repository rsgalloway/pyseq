# Setup and Distribution

This guide covers the environment configuration and source distribution options
that support more customized pyseq setups.

## Environment

PySeq reads configuration from standard environment variables. The repository
includes a `pyseq.env` example [envstack](https://github.com/rsgalloway/envstack)
file for users who want to manage those variables externally.

## Distribution

If installing from source you can use [distman](https://github.com/rsgalloway/distman)
to install PySeq using the provided `dist.json` file:

```bash
$ pip install -U distman
$ dist [-d]
```

Using distman will deploy the targets defined in the `dist.json` file to the
root folder defined by `${DEPLOY_ROOT}`.
