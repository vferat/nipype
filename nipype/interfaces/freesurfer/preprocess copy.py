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
    input = File(
        argstr="--i %s",
        usedefault=False,
        desc="Volume to deface.",
        exists=True
    )
    output = File(
        argstr="--o %s",
        usedefault=False,
        desc="defaced input.",
        exists=False
    )
    facemask = File(
        argstr="--facemask %s",
        usedefault=False,
        desc="facemask.",
        exists=True
    )
    odir = Directory(
        argstr="--odir %s",
        usedefault=False,
        desc="output dir.",
        exists=False
    )
    xmask = File(
        argstr="--xmask %s",
        usedefault=False,
        desc="Exclusion mask.",
        exists=True
    )
    imconvert = File(
        argstr="--imconvert %s",
        usedefault=False,
        desc="Path to imagemagik convert binary (for pics).",
        exists=True
    )
    # samseg
    samseg_ndilations = traits.Int(argstr="--xmask-samseg %s", desc="segment input using samseg (14GB, +~20-40min)")
    samseg_json = File(
        argstr="--samseg-json %s",
        usedefault=False,
        desc="json: configure samseg",
        exists=True
    )
    samesegfast = traits.Bool(argstr="--samseg-fast", desc="configure samseg to run quickly; sets ndil=1 (default)",
                              xor=['nosamesegfast'])
    nosamesegfast = traits.Bool(argstr="--samseg-fast", desc="configure samseg to run quickly; sets ndil=1 (default)",
                                xor=['samesegfast'])
    # synthseg
    synthseg_ndilations = traits.Int(argstr="--xmask-synthseg %s", desc="segment input using synthseg (35GB, +~20min)")
    # fill
    fill_zero = traits.Bool(argstr="--fill-zero")
    # Deface geometry
    noears = traits.Bool(argstr="--no-ears", desc="do not include ears in the defacing")
    backofhead = traits.Bool(argstr="--back-of-head", desc="include back of head in the defacing")
    forehead = traits.Bool(argstr="--forehead", desc="include forehead in the defacing (risks removing brain)")
    # Post proc
    pics = traits.Bool(argstr="--pics", desc="take pics")
    nopost = traits.Bool(argstr="--no-post", desc="do not make a head surface after defacing")
    threads = traits.Int(argstr="--threads", desc="nthreads")
    force = traits.Bool(argstr="--force", desc="force reprocessing (not applicable if --odir has not been used)",
                      requires=['odir'])
    # Output type
    nii = traits.Bool(argstr="--nii", desc="use nifti format as output (only when output files are not specified)",
                      xor=['output', 'niigz', 'mgz'])
    niigz = traits.Bool(argstr="--nii.gz", desc="use compressed nifti format as output (only when output files are not specified)",
                      xor=['output', 'nii', 'mgz'])
    mgz = traits.Bool(argstr="--nii.gz", desc="use compressed mgh format as output.",
                      xor=['output', 'nii', 'niigz'])


class MidefaceOutputSpec(TraitedSpec):
    outfile = File(exists=True, desc="text file containing dicom information")


class Mideface(FSCommand):
    """Uses midefacer a minimally invasive defacing tool.

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

    _cmd = "mideface"
    input_spec = MidefaceInputSpec
    output_spec = MidefaceOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.dicom_info_file):
            outputs["dicom_info_file"] = os.path.join(
                os.getcwd(), self.inputs.dicom_info_file
            )
        return outputs
