#!/usr/bin/env bash
ps aux | grep "manager_supervisord" | grep -v grep| cut -c 9-15 | xargs kill -9
ps aux | grep "celery_task" | grep -v grep| cut -c 9-15 | xargs kill -9
ps aux | grep "run_manager_web" | grep -v grep| cut -c 9-15 | xargs kill -9
ps aux | grep "run_backend_manager" | grep -v grep| cut -c 9-15 | xargs kill -9
