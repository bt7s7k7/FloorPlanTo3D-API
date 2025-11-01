#!/bin/env bash
tar cvzf - maskrcnn_15_epochs.h5 | split --bytes=75MB - maskrcnn_15_epochs.h5.tar.gz.