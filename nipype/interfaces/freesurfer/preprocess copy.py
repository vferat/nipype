# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by FreeSurfer
"""
import os
import os.path as op
from glob import glob
import shutil
import sys

from looseversion import LooseVersion
import numpy as np
from nibabel import load

from ... import logging
from ...utils.filemanip import fname_presuffix, check_depends
from ..io import FreeSurferSource
from ..base import (
    TraitedSpec,
    File,
    traits,
    Directory,
    InputMultiPath,
    OutputMultiPath,
    CommandLine,
    CommandLineInputSpec,
    isdefined,
)
from .base import FSCommand, FSTraitedSpec, FSTraitedSpecOpenMP, FSCommandOpenMP, Info
from .utils import copy2subjdir

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")

# Keeping this to avoid breaking external programs that depend on it, but
# this should not be used internally
FSVersion = Info.looseversion().vstring


class MidefaceInputSpec(FSTraitedSpec):
    dicom_info_file = File(
        argstr="--i %s",
        usedefault=False,
        desc="file to which results are written",
    )
    sortbyrun = traits.Bool(argstr="--sortbyrun", desc="assign run numbers")
    summarize = traits.Bool(
        argstr="--summarize", desc="only print out info for run leaders"
    )


class MidefaceOutputSpec(TraitedSpec):
    dicom_info_file = File(exists=True, desc="text file containing dicom information")


class Mideface(FSCommand):
    """Uses mri_parse_sdcmdir to get information from dicom directories

    Examples
    --------

    >>> from nipype.interfaces.freesurfer import ParseDICOMDir
    >>> dcminfo = ParseDICOMDir()
    >>> dcminfo.inputs.dicom_dir = '.'
    >>> dcminfo.inputs.sortbyrun = True
    >>> dcminfo.inputs.summarize = True
    >>> dcminfo.cmdline
    'mri_parse_sdcmdir --d . --o dicominfo.txt --sortbyrun --summarize'

    """

    _cmd = "mri_parse_sdcmdir"
    input_spec = MidefaceInputSpec
    output_spec = MidefaceOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.dicom_info_file):
            outputs["dicom_info_file"] = os.path.join(
                os.getcwd(), self.inputs.dicom_info_file
            )
        return outputs
