#!/usr/bin/env bash
curl -sf http://127.0.0.1:8000/api/health || exit 1
