import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            with_setup, TraitError, parametric, skipif)

from nipype.utils.filemanip import split_filename
import nipype.interfaces.fsl.preprocess as fsl
from nipype.interfaces.fsl import Info
from nipype.interfaces.base import InterfaceResult, File
from nipype.interfaces.fsl import check_fsl
from nipype.interfaces.traits import Undefined

def fsl_name(obj, fname):
    """Create valid fsl name, including file extension for output type.
    """
    ext = Info.output_type_to_ext(obj.inputs.output_type)
    return fname + ext

tmp_infile = None
tmp_dir = None
def setup_infile():
    global tmp_infile, tmp_dir
    ext = Info.output_type_to_ext(Info.output_type())
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo' + ext)
    file(tmp_infile, 'w')
    return tmp_infile, tmp_dir

def teardown_infile(tmp_dir):
    shutil.rmtree(tmp_dir)

# test BET
#@with_setup(setup_infile, teardown_infile)
#broken in nose with generators
def test_bet():
    tmp_infile, tp_dir = setup_infile()
    better = fsl.BET()
    yield assert_equal, better.cmd, 'bet'

    # Test raising error with mandatory args absent
    yield assert_raises, ValueError, better.run

    # Test generated outfile name
    better.inputs.in_file = tmp_infile
    outfile = fsl_name(better, 'foo_brain')
    outpath = os.path.join(os.getcwd(), outfile)
    realcmd = 'bet %s %s' % (tmp_infile, outpath)
    yield assert_equal, better.cmdline, realcmd
    # Test specified outfile name
    outfile = fsl_name(better, '/newdata/bar')
    better.inputs.out_file = outfile
    realcmd = 'bet %s %s' % (tmp_infile, outfile)
    yield assert_equal, better.cmdline, realcmd

    # infile foo.nii doesn't exist
    def func():
        better.run(in_file='foo.nii', out_file='bar.nii')
    yield assert_raises, TraitError, func

    # .run() based parameter setting
    better = fsl.BET()
    better.inputs.frac = 0.40
    outfile = fsl_name(better, 'outfile')
    betted = better.run(in_file=tmp_infile, out_file=outfile)
    yield assert_equal, betted.interface.inputs.in_file, tmp_infile
    yield assert_equal, betted.interface.inputs.out_file, outfile
    realcmd = 'bet %s %s -f 0.40' % (tmp_infile, outfile)
    yield assert_equal, betted.runtime.cmdline, realcmd

    # Our options and some test values for them
    # Should parallel the opt_map structure in the class for clarity
    opt_map = {
        'outline':            ('-o', True),
        'mask':               ('-m', True),
        'skull':              ('-s', True),
        'no_output':           ('-n', True),
        'frac':               ('-f 0.40', 0.4),
        'vertical_gradient':  ('-g 0.75', 0.75),
        'radius':             ('-r 20', 20),
        'center':             ('-c 54 75 80', [54, 75, 80]),
        'threshold':          ('-t', True),
        'mesh':               ('-e', True),
        #'verbose':            ('-v', True),
        #'flags':              ('--i-made-this-up', '--i-made-this-up'),
            }
    # Currently we don't test -R, -S, -B, -Z, -F, -A or -A2

    # test each of our arguments
    better = fsl.BET()
    outfile = fsl_name(better, 'foo_brain')
    outpath = os.path.join(os.getcwd(), outfile)
    for name, settings in opt_map.items():
        better = fsl.BET(**{name: settings[1]})
        # Add mandatory input
        better.inputs.in_file = tmp_infile
        realcmd =  ' '.join([better.cmd, tmp_infile, outpath, settings[0]])
        yield assert_equal, better.cmdline, realcmd
    teardown_infile(tmp_dir)
    
# test fast
def test_fast():
    tmp_infile, tp_dir = setup_infile()
    faster = fsl.FAST()
    faster.inputs.verbose = True
    fasted = faster.run(in_files=tmp_infile)
    fasted2 = faster.run(in_files=[tmp_infile, tmp_infile])

    yield assert_equal, faster.cmd, 'fast'
    yield assert_equal, faster.inputs.verbose, True
    yield assert_equal, faster.inputs.manual_seg , Undefined
    yield assert_not_equal, faster, fasted
    yield assert_equal, fasted.runtime.cmdline, 'fast -v %s'%(tmp_infile)
    yield assert_equal, fasted2.runtime.cmdline, 'fast -v %s %s'%(tmp_infile,
                                                                  tmp_infile)

    faster = fsl.FAST()
    faster.inputs.in_files = tmp_infile
    yield assert_equal, faster.cmdline, 'fast %s'%(tmp_infile)
    faster.inputs.in_files = [tmp_infile, tmp_infile]
    yield assert_equal, faster.cmdline, 'fast %s %s'%(tmp_infile, tmp_infile)

    # Our options and some test values for them
    # Should parallel the opt_map structure in the class for clarity
    opt_map = {'number_classes':       ('-n 4', 4),
               'bias_iters':           ('-I 5', 5),
               'bias_lowpass':         ('-l 15', 15),
               'img_type':             ('-t 2', 2),
               'init_seg_smooth':      ('-f 0.035', 0.035),
               'segments':             ('-g', True),
               'init_transform':       ('-a %s'%(tmp_infile), '%s'%(tmp_infile)),
               'other_priors':         ('-A %s %s %s'%(tmp_infile, tmp_infile,
                                                       tmp_infile),
                                        (['%s'%(tmp_infile),
                                          '%s'%(tmp_infile),
                                          '%s'%(tmp_infile)])),
               'no_pve':                ('--nopve', True),
               'output_biasfield':     ('-b', True),
               'output_biascorrected': ('-B', True),
               'no_bias':               ('-N', True),
               'out_basename':         ('-o fasted', 'fasted'),
               'use_priors':           ('-P', True),
               'segment_iters':        ('-W 14', 14),
               'mixel_smooth':         ('-R 0.25', 0.25),
               'iters_afterbias':      ('-O 3', 3),
               'hyper':                ('-H 0.15', 0.15),
               'verbose':              ('-v', True),
               'manual_seg':            ('-s %s'%(tmp_infile),
                       '%s'%(tmp_infile)),
               'probability_maps':     ('-p', True),
              }

    # test each of our arguments
    for name, settings in opt_map.items():
        faster = fsl.FAST(in_files=tmp_infile, **{name: settings[1]})
        yield assert_equal, faster.cmdline, ' '.join([faster.cmd,
                                                      settings[0],
                                                      tmp_infile])
    teardown_infile(tmp_dir)
    
def setup_flirt():
    ext = Info.output_type_to_ext(Info.output_type())
    tmpdir = tempfile.mkdtemp()
    _, infile = tempfile.mkstemp(suffix = ext, dir = tmpdir)
    _, reffile = tempfile.mkstemp(suffix = ext, dir = tmpdir)
    return tmpdir, infile, reffile

def teardown_flirt(tmpdir):
    shutil.rmtree(tmpdir)

@parametric
def test_flirt():
    # setup
    tmpdir, infile, reffile = setup_flirt()
    
    flirter = fsl.FLIRT()
    yield assert_equal(flirter.cmd, 'flirt')

    flirter.inputs.bins = 256
    flirter.inputs.cost = 'mutualinfo'

    flirted = flirter.run(in_file=infile, reference=reffile,
                          out_file='outfile', out_matrix_file='outmat.mat')
    flirt_est = flirter.run(in_file=infile, reference=reffile,
                            out_matrix_file='outmat.mat')
    yield assert_not_equal(flirter, flirted)
    yield assert_not_equal(flirted, flirt_est)

    yield assert_equal(flirter.inputs.bins, flirted.interface.inputs.bins)
    yield assert_equal(flirter.inputs.cost, flirt_est.interface.inputs.cost)
    realcmd = 'flirt -in %s -ref %s -out outfile -omat outmat.mat ' \
        '-bins 256 -cost mutualinfo' % (infile, reffile)
    yield assert_equal(flirted.runtime.cmdline, realcmd)

    flirter = fsl.FLIRT()
    # infile not specified
    yield assert_raises(ValueError, flirter.run)
    flirter.inputs.in_file = infile
    # reference not specified
    yield assert_raises(ValueError, flirter.run)
    flirter.inputs.reference = reffile
    res = flirter.run()
    # Generate outfile and outmatrix
    pth, fname, ext = split_filename(infile)
    outfile = '%s_flirt%s' % (fname, ext)
    outfile = os.path.join(os.getcwd(), outfile)
    outmat = '%s_flirt.mat' % fname
    outmat = os.path.join(os.getcwd(), outmat)
    realcmd = 'flirt -in %s -ref %s -out %s -omat %s' % (infile, reffile,
                                                         outfile, outmat)
    yield assert_equal(res.interface.cmdline, realcmd)

    _, tmpfile = tempfile.mkstemp(suffix = '.nii', dir = tmpdir)
    # Loop over all inputs, set a reasonable value and make sure the
    # cmdline is updated correctly.
    for key, trait_spec in sorted(fsl.FLIRT.input_spec().traits().items()):
        # Skip mandatory inputs and the trait methods
        if key in ('trait_added', 'trait_modified', 'in_file', 'reference',
                   'environ', 'output_type', 'out_file', 'out_matrix_file',
                   'in_matrix_file'):
            continue
        param = None
        value = None
        if key == 'args':
            param = '-v'
            value = '-v'
        elif isinstance(trait_spec.trait_type, File):
            value = tmpfile
            param = trait_spec.argstr  % value
        elif trait_spec.default is False:
            param = trait_spec.argstr
            value = True
        elif key in ('searchr_x', 'searchr_y', 'searchr_z'):
            value = [-45, 45]
            param = trait_spec.argstr % ' '.join(str(elt) for elt in value)
        else:
            value = trait_spec.default
            param = trait_spec.argstr % value
        cmdline = 'flirt -in %s -ref %s' % (infile, reffile)
        # Handle autogeneration of outfile
        pth, fname, ext = split_filename(infile)
        outfile = '%s_flirt%s' % (fname, ext)
        outfile = os.path.join(os.getcwd(), outfile)
        outfile = ' '.join(['-out', outfile])
        # Handle autogeneration of outmatrix
        outmatrix = '%s_flirt.mat' % fname
        outmatrix = os.path.join(os.getcwd(), outmatrix)
        outmatrix = ' '.join(['-omat', outmatrix])
        # Build command line
        cmdline = ' '.join([cmdline, outfile, outmatrix, param])
        flirter = fsl.FLIRT(in_file = infile, reference = reffile)
        setattr(flirter.inputs, key, value)
        yield assert_equal(flirter.cmdline, cmdline)

    # Test OutputSpec
    flirter = fsl.FLIRT(in_file = infile, reference = reffile)
    pth, fname, ext = split_filename(infile)
    flirter.inputs.out_file = ''.join(['foo', ext])
    flirter.inputs.out_matrix_file = ''.join(['bar', ext])
    outs = flirter._list_outputs()
    yield assert_equal(outs['out_file'], flirter.inputs.out_file)
    yield assert_equal(outs['out_matrix_file'], flirter.inputs.out_matrix_file)

    teardown_flirt(tmpdir)

def test_applyxfm():
    # ApplyXFM subclasses FLIRT, but doesnt change anything.
    # setup
    tmpdir, infile, reffile = setup_flirt()

    outname = 'xfm_subj.nii'
    
    flt = fsl.ApplyXfm(in_file = infile,
                       in_matrix_file = infile,
                       out_file = outname,
                       reference = reffile,
                       apply_xfm = True)
    _, nme = os.path.split(infile)
    tmpoutfile = os.path.join(os.getcwd(),nme)
    outfile = flt._gen_fname(tmpoutfile, suffix='_flirt')
    outfile = outfile.replace(Info.output_type_to_ext(Info.output_type()),
                              '.mat')
    yield assert_equal, flt.cmdline, \
        'flirt -in %s -ref %s -out %s ' \
        '-omat %s -applyxfm '\
        '-init %s'%(infile, reffile,
                     outname, outfile,
                     infile)
    flt = fsl.ApplyXfm(apply_xfm=True)
    yield assert_raises, ValueError, flt.run
    flt.inputs.in_file = infile
    flt.inputs.out_file = 'xfm_subj.nii'
    # reference not specified
    yield assert_raises, ValueError, flt.run
    flt.inputs.reference = reffile
    # in_matrix not specified
    yield assert_raises, ValueError, flt.run

    

# Mcflirt
def test_mcflirt():
    tmpdir, infile, reffile = setup_flirt()
    
    frt = fsl.MCFLIRT()
    yield assert_equal, frt.cmd, 'mcflirt'
    # Test generated outfile name

    frt.inputs.in_file = infile
    outfile = os.path.join(os.getcwd(), 'foo_mcf.nii')
    realcmd = 'mcflirt -in ' + infile + ' -out ' + outfile
    yield assert_equal, frt.cmdline, realcmd
    # Test specified outfile name
    outfile = '/newdata/bar.nii'
    frt.inputs.out_file = outfile
    realcmd = 'mcflirt -in ' + infile + ' -out ' + outfile
    yield assert_equal, frt.cmdline, realcmd

    opt_map = {
        'out_file':     ('-out bar.nii', 'bar.nii'),
        'cost':        ('-cost mutualinfo', 'mutualinfo'),
        'bins':        ('-bins 256', 256),
        'dof':         ('-dof 6', 6),
        'refvol':      ('-refvol 2', 2),
        'scaling':     ('-scaling 6.00', 6.00),
        'smooth':      ('-smooth 1.00', 1.00),
        'rotation':    ('-rotation 2', 2),
        'verbose':     ('-verbose', True),
        'stages':      ('-stages 3', 3),
        'init':        ('-init matrix.mat', 'matrix.mat'),
        'usegradient': ('-gdt', True),
        'usecontour':  ('-edge', True),
        'meanvol':     ('-meanvol', True),
        'statsimgs':   ('-stats', True),
        'savemats':    ('-mats', True),
        'saveplots':   ('-plots', True),
        'report':      ('-report', True),
        }

    for name, settings in opt_map.items():
        fnt = fsl.MCFLIRT(**{name : settings[1]})
        yield assert_equal, fnt.cmdline, ' '.join([fnt.cmd, settings[0]])

    # Test error is raised when missing required args
    fnt = fsl.MCFLIRT()
    yield assert_raises, AttributeError, fnt.run
    # Test run result
    fnt = fsl.MCFLIRT()
    fnt.inputs.in_file = 'foo.nii'
    res = fnt.run()
    yield assert_equal, type(res), InterfaceResult
    res = fnt.run(in_file='bar.nii')
    yield assert_equal, type(res), InterfaceResult
    teardown_flirt(tmpdir)

#test fnirt
def test_fnirt():
    fnirt = fsl.FNIRT()
    yield assert_equal, fnirt.cmd, 'fnirt'

    # Test inputs with variable number of values
    fnirt.inputs.sub_sampling = [8, 6, 4]
    yield assert_equal, fnirt.inputs.sub_sampling, [8, 6, 4]
    fnirtd = fnirt.run(in_file='infile', reference='reference')
    realcmd = 'fnirt --in=infile --ref=reference --subsamp=8,6,4'
    yield assert_equal, fnirtd.runtime.cmdline, realcmd

    fnirt2 = fsl.FNIRT(sub_sampling=[8, 2])
    fnirtd2 = fnirt2.run(in_file='infile', reference='reference')
    realcmd = 'fnirt --in=infile --ref=reference --subsamp=8,2'
    yield assert_equal, fnirtd2.runtime.cmdline, realcmd

    # Test case where input that can be a list is just a single value
    params = [('sub_sampling', '--subsamp'),
              ('max_iter', '--miter'),
              ('referencefwhm', '--reffwhm'),
              ('imgfwhm', '--infwhm'),
              ('lambdas', '--lambda'),
              ('estintensity', '--estint'),
              ('applyrefmask', '--applyrefmask'),
              ('applyimgmask', '--applyinmask')]
    for item, flag in params:


        if item in ('sub_sampling', 'max_iter',
                    'referencefwhm', 'imgfwhm',
                    'lambdas', 'estintensity'):
            fnirt = fsl.FNIRT(**{item : 5})
            cmd = 'fnirt %s=%d' % (flag, 5)
        else:
            fnirt = fsl.FNIRT(**{item : 5})
            cmd = 'fnirt %s=%f' % (flag, 5)
        yield assert_equal, fnirt.cmdline, cmd

    # Test error is raised when missing required args
    fnirt = fsl.FNIRT()
    yield assert_raises, AttributeError, fnirt.run
    fnirt.inputs.in_file = 'foo.nii'
    # I don't think this is correct. See FNIRT documentation -DJC
    # yield assert_raises, AttributeError, fnirt.run
    fnirt.inputs.reference = 'mni152.nii'
    res = fnirt.run()
    yield assert_equal, type(res), InterfaceResult

    opt_map = {
        'affine':           ('--aff=affine.mat', 'affine.mat'),
        'initwarp':         ('--inwarp=warp.mat', 'warp.mat'),
        'initintensity':    ('--intin=inten.mat', 'inten.mat'),
        'configfile':       ('--config=conf.txt', 'conf.txt'),
        'referencemask':    ('--refmask=ref.mat', 'ref.mat'),
        'imagemask':        ('--inmask=mask.nii', 'mask.nii'),
        'fieldcoeff_file':  ('--cout=coef.txt', 'coef.txt'),
        'outimage':         ('--iout=out.nii', 'out.nii'),
        'fieldfile':        ('--fout=fld.txt', 'fld.txt'),
        'jacobianfile':     ('--jout=jaco.txt', 'jaco.txt'),
        'reffile':          ('--refout=refout.nii', 'refout.nii'),
        'intensityfile':    ('--intout=intout.txt', 'intout.txt'),
        'logfile':          ('--logout=log.txt', 'log.txt'),
        'verbose':          ('--verbose', True),
        'flags':            ('--fake-flag', '--fake-flag')}

    for name, settings in opt_map.items():
        fnirt = fsl.FNIRT(**{name : settings[1]})
        yield assert_equal, fnirt.cmdline, ' '.join([fnirt.cmd, settings[0]])

def test_applywarp():
    opt_map = {
        'in_file':            ('--in=foo.nii', 'foo.nii'),
        'out_file':           ('--out=bar.nii', 'bar.nii'),
        'reference':         ('--ref=refT1.nii', 'refT1.nii'),
        'fieldfile':         ('--warp=warp_field.nii', 'warp_field.nii'),
        'premat':            ('--premat=prexform.mat', 'prexform.mat'),
        'postmat':           ('--postmat=postxform.mat', 'postxform.mat')
        }

    for name, settings in opt_map.items():
        awarp = fsl.ApplyWarp(**{name : settings[1]})
        if name == 'in_file':
            outfile = os.path.join(os.getcwd(), 'foo_warp.nii')
            realcmd = 'applywarp --in=foo.nii --out=%s' % outfile
            yield assert_equal, awarp.cmdline, realcmd
        else:
            yield assert_equal, awarp.cmdline, \
                ' '.join([awarp.cmd, settings[0]])
