from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import itertools

import torch
import torch.jit
from torch.autograd import Variable
import torch.autograd.function as function

import onnx
import onnx_caffe2.backend as c2


torch.set_default_tensor_type('torch.FloatTensor')
try:
    import torch
except ImportError:
    print('Cannot import torch, hence caffe2-torch test will not run.')
    sys.exit(0)


def _flatten(x):
    return tuple(function._iter_filter(lambda o: isinstance(o, Variable) or torch.is_tensor(o))(x))


def test_embed_params(proto, model, input, state_dict=None, use_gpu=True):
    """
    This is only a helper debug function so we can test embed_params=False
    case as well on pytorch front
    This should likely be removed from the release version of the code
    """
    device = 'CPU'
    if use_gpu:
      device = 'CUDA'
    model_def = onnx.ModelProto.FromString(proto)
    onnx.checker.check_model(model_def)
    prepared = c2.prepare(model_def, device=device)

    if state_dict:
      parameters = []
      # Passed in state_dict may have a different order.  Make
      # sure our order is consistent with the model's order.
      # TODO: Even better: keyword arguments!
      for k in model.state_dict():
        parameters.append(state_dict[k])
    else:
      parameters = model.state_dict().values()

    W = {}
    for k, v in zip(model_def.graph.input, _flatten((input, parameters))):
      if isinstance(v, Variable):
        W[k.name] = v.data.cpu().numpy()
      else:
        W[k.name] = v.cpu().numpy()

    caffe2_out = prepared.run(inputs=W)

    return caffe2_out
