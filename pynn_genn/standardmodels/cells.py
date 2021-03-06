# encoding: utf-8
"""
Standard cells for the GeNN module.

:copyright: Copyright 2006-2016 by the PyNN team, see AUTHORS.
:license: CeCILL, see LICENSE for details.
"""

from copy import deepcopy
from functools import partial
import numpy as np
import lazyarray as la
from pyNN.standardmodels import cells, build_translations
from ..simulator import state
import logging
from ..model import GeNNStandardCellType, GeNNDefinitions
from pygenn.genn_model import create_custom_neuron_class

logger = logging.getLogger("PyNN")

# Function to convert time constants to exponential decay
def tau_to_decay(tau_param_name, **kwargs):
    return la.exp(-state.dt / kwargs[tau_param_name])

def tau_to_init(tau_param_name, **kwargs):
    tau = kwargs[tau_param_name]
    
    init = 1.0 - la.exp(-state.dt / tau)
    return init * (tau / state.dt)

# Function to convert mean 'rate' parameter
# to mean interspike interval (in timesteps)
def rate_to_isi(rate_param_name, **kwargs):
    return 1000.0 / (kwargs[rate_param_name] * state.dt)

# Function to convert mean interspike interval 
# 'isi' (in timesteps) to mean rate in Hz
def isi_to_rate(isi_param_name, **kwargs):
    return 1000.0 / (kwargs[isi_param_name] * state.dt)

# Function to convert milliseconds to simulation timesteps
def ms_to_timesteps(ms_param_name, **kwargs):
    return kwargs[ms_param_name] / state.dt

# Function to convert simulation timesteps to milliseconds
def timesteps_to_ms(timestep_param_name, **kwargs):
    return kwargs[timestep_param_name] * state.dt

genn_neuron_defs = {}

genn_neuron_defs["IF"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            if ($(RefracTime) <= 0.0) {
                scalar alpha = (($(Isyn) + $(Ioffset)) * $(Rmembrane)) + $(Vrest);
                $(V) = alpha - ($(ExpTC) * (alpha - $(V)));
            }
            else {
                $(RefracTime) -= DT;
            }
        """,

        "threshold_condition_code" : "$(RefracTime) <= 0.0 && $(V) >= $(Vthresh)",

        "reset_code" : """
            $(V) = $(Vreset);
            $(RefracTime) = $(TauRefrac);
        """,

        "var_name_types" : [
            ("V", "scalar"),
            ("RefracTime", "scalar")],
        
        "param_name_types": {
            "Rmembrane": "scalar",  # Membrane resistance
            "ExpTC": "scalar",       # Membrane time constant [ms]
            "Vrest": "scalar",      # Resting membrane potential [mV]
            "Vreset": "scalar",     # Reset voltage [mV]
            "Vthresh": "scalar",    # Spiking threshold [mV]
            "Ioffset": "scalar",    # Offset current
            "TauRefrac": "scalar"}
    },
    translations = (
        ("v_rest",     "Vrest"),
        ("v_reset",    "Vreset"),
        ("cm",         "Rmembrane",     "tau_m / cm", ""),
        ("tau_m",      "ExpTC",         partial(tau_to_decay, "tau_m"), None),
        ("tau_refrac", "TauRefrac"),
        ("v_thresh",   "Vthresh"),
        ("i_offset",   "Ioffset"),
        ("v",          "V"),
    ),
    extra_param_values = {
        "RefracTime" : 0.0,
    })

genn_neuron_defs["Adapt"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            if ($(RefracTime) <= 0.0) {
                scalar alpha = (($(Isyn) + $(Ioffset) - $(GRr) * ($(V) - $(ERr)) - $(GSfa) * ($(V) - $(ESfa))) * $(Rmembrane)) + $(Vrest);
                $(V) = alpha - ($(ExpTC) * (alpha - $(V)));
                $(GSfa) *= $(ExpSFA);
                $(GRr) *= $(ExpRr);
            }
            else {
                $(RefracTime) -= DT;
            }
        """,

        "threshold_condition_code" : "$(RefracTime) <= 0.0 && $(V) >= $(Vthresh)",

        "reset_code" : """
            $(V) = $(Vreset);
            $(RefracTime) = $(TauRefrac);
            $(GSfa) += $(QSfa);
            $(GRr) += $(QRr);
        """,

        "var_name_types" : [
            ("V", "scalar"),
            ("RefracTime", "scalar"),
            ("GSfa", "scalar"),
            ("GRr", "scalar")],
        
        "param_name_types": {
            "Rmembrane": "scalar",  # Membrane resistance
            "ExpTC": "scalar",      # Membrane decay
            "Vrest": "scalar",      # Resting membrane potential [mV]
            "Vreset": "scalar",     # Reset voltage [mV]
            "Vthresh": "scalar",    # Spiking threshold [mV]
            "Ioffset": "scalar",    # Offset current [nA]
            "TauRefrac": "scalar",  # Refractoriness [ms]
            "ExpSFA": "scalar",     # Spike frequency adaptation decay
            "ExpRr": "scalar",      # Relative refractoriness decay
            "ESfa": "scalar",       # Spike frequency adaptation reversal potention [mV]
            "ERr": "scalar",        # Relative refractoriness reversal potention [mV]
            "QSfa": "scalar",       # Quantal spike frequency adaptation conductance increase [pS]
            "QRr": "scalar"}        # Quantal relative refractoriness conductance increase [pS]
    },
    translations = (
        ("v_rest",     "Vrest"),
        ("v_reset",    "Vreset"),
        ("cm",         "Rmembrane",     "tau_m / cm",   ""),
        ("tau_m",      "ExpTC",         partial(tau_to_decay, "tau_m"),    None),
        ("tau_refrac", "TauRefrac"),
        ("v_thresh",   "Vthresh"),
        ("i_offset",   "Ioffset"),
        ("v",          "V"),
        ("tau_sfa",    "ExpSFA",        partial(tau_to_decay, "tau_sfa"),  None),
        ("e_rev_sfa",  "ESfa"),
        ("tau_rr",     "ExpRr",         partial(tau_to_decay, "tau_rr"),   None),
        ("e_rev_rr",   "ERr"),
        ("g_s",        "GSfa", 0.001),
        ("g_r",        "GRr", 0.001),
        ("q_sfa",      "QSfa", 0.001),
        ("q_rr",       "QRr", 0.001)
    ),
    extra_param_values = {
        "RefracTime" : 0.0,
    })

#  genn_neuron_defs["GIF"] = GeNNNeuronDefinitions(
#      # definitions
#      {
#          "simCode" : """
#
#          """,
#
#          "thresholdConditionCode" : "",
#
#          "resetCode" : "",
#
#          "paramNames"

genn_neuron_defs["AdExp"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            #define DV(V, W) (1.0 / $(TauM)) * (-((V) - $(Vrest)) + ($(deltaT) * exp(((V) - $(vThresh)) / $(deltaT)))) + (i - (W)) / $(C)
            #define DV_DELTA_T_ZERO(V, W) (1.0 / $(TauM)) * (-((V) - $(Vrest))) + (i - (W)) / $(C)
            #define DW(V, W) (1.0 / $(tauW)) * (($(a) * (V - $(Vrest))) - W)

            // If voltage is above artificial spike height, reset it
            if($(V) >= $(vSpike)) {
                $(V) = $(vReset);
            }

            // Calculate RK4 terms
            const scalar i = $(Isyn) + $(iOffset);
            scalar v1, w1, v2, w2, v3, w3, v4, w4;
            if($(deltaT) == 0.0) {
                v1 = DV_DELTA_T_ZERO($(V), $(W));
                w1 = DW($(V), $(W));
                v2 = DV_DELTA_T_ZERO($(V) + (DT * 0.5 * v1), $(W) + (DT * 0.5 * w1));
                w2 = DW($(V) + (DT * 0.5 * v1), $(W) + (DT * 0.5 * w1));
                v3 = DV_DELTA_T_ZERO($(V) + (DT * 0.5 * v2), $(W) + (DT * 0.5 * w2));
                w3 = DW($(V) + (DT * 0.5 * v2), $(W) + (DT * 0.5 * w2));
                v4 = DV_DELTA_T_ZERO($(V) + (DT * v3), $(W) + (DT * w3));
                w4 = DW($(V) + (DT * v3), $(W) + (DT * w3));
            }
            else {
                v1 = DV($(V), $(W));
                w1 = DW($(V), $(W));
                v2 = DV($(V) + (DT * 0.5 * v1), $(W) + (DT * 0.5 * w1));
                w2 = DW($(V) + (DT * 0.5 * v1), $(W) + (DT * 0.5 * w1));
                v3 = DV($(V) + (DT * 0.5 * v2), $(W) + (DT * 0.5 * w2));
                w3 = DW($(V) + (DT * 0.5 * v2), $(W) + (DT * 0.5 * w2));
                v4 = DV($(V) + (DT * v3), $(W) + (DT * w3));
                w4 = DW($(V) + (DT * v3), $(W) + (DT * w3));
            }

            // If we're not in refractory period, update V
            if ($(RefracTime) <= 0.0) {
                $(V) += (DT / 6.0) * (v1 + (2.0f * (v2 + v3)) + v4);
            }
            else {
                $(RefracTime) -= DT;
            }

            // If we're not above peak, update w
            // **NOTE** it's not safe to do this at peak as wn may well be huge
            if($(V) <= -40.0) {
                $(W) += (DT / 6.0) * (w1 + (2.0 * (w2 + w3)) + w4);
            }
        """,

        "threshold_condition_code" : "($(deltaT) == 0 && $(V) > $(vThresh)) || ($(deltaT) > 0.0 && $(V) > -40)",

        "reset_code" : """
            // **NOTE** we reset v to arbitrary plotting peak rather than to actual reset voltage
            $(V) = $(vSpike);
            $(W) += ($(b));
            $(RefracTime) = $(TauRefrac);
        """,

        "var_name_types" : [
            ("V", "scalar"),
            ("W", "scalar"),# adaptation current, [nA]
            ("RefracTime", "scalar")],
        
        "param_name_types": {
            "C": "scalar",        # Membrane capacitance [nF]
            "TauM": "scalar",     # Membrane time constant [ms]
            "TauRefrac": "scalar",  # Refractoriness [ms]
            "Vrest": "scalar",    # Resting membrane voltage (Leak reversal potential) [mV]
            "deltaT": "scalar",   # Slope factor [mV]
            "vThresh": "scalar",  # Threshold voltage [mV]
            "vSpike": "scalar",   # Artificial spike height [mV]
            "vReset": "scalar",   # Reset voltage [mV]
            "tauW": "scalar",     # Adaption time constant [ms]
            "a": "scalar",        # Subthreshold adaption [pS]
            "b": "scalar",        # Spike-triggered adaptation [nA]
            "iOffset": "scalar"}, # Offset current [nA]
    },
    translations = (
        ("cm",         "C"),
        ("tau_refrac", "TauRefrac"),
        ("v_spike",    "vSpike"),
        ("v_reset",    "vReset"),
        ("v_rest",     "Vrest"),
        ("tau_m",      "TauM"),
        ("i_offset",   "iOffset"),
        ("a",          "a", 0.001),
        ("b",          "b"),
        ("delta_T",    "deltaT"),
        ("tau_w",      "tauW"),
        ("v_thresh",   "vThresh"),
        ("v",          "V"),
        ("w",          "W"),
    ),
    extra_param_values = {
        "RefracTime" : 0.0,
    })

genn_neuron_defs["Poisson"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            oldSpike = false;
            if($(timeStepToSpike) <= 0.0f) {
                $(timeStepToSpike) += $(isi) * $(gennrand_exponential);
            }
            $(timeStepToSpike) -= 1.0;
        """,

        "threshold_condition_code" : "$(t) >= $(spikeStart) && $(t) < $(spikeStart) + $(duration) && $(timeStepToSpike) <= 0.0",

        "var_name_types": [
            ("timeStepToSpike", "scalar")],
        
        "param_name_types": {
            "isi": "scalar",
            "spikeStart": "scalar",
            "duration": "scalar"},
    },
    translations = (
        ("rate",     "isi",         partial(rate_to_isi, "rate"),  partial(isi_to_rate, "isi")),
        ("start",    "spikeStart"),
        ("duration", "duration")
    ),
    extra_param_values = {
        "timeStepToSpike" : 0.0,
    })

genn_neuron_defs["PoissonRef"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            oldSpike = false;
            if($(timeStepToSpike) <= 0.0 ) {
                $(timeStepToSpike) += ($(isi)-$(TauRefrac)) * $(gennrand_exponential) + $(TauRefrac);
            }
            $(timeStepToSpike) -= 1.0;
        """,

        "threshold_condition_code" : "$(t) >= $(spikeStart) && $(t) < $(spikeStart) + $(duration) && $(timeStepToSpike) <= 0.0",

        "var_name_types" : [
            ("timeStepToSpike", "scalar"),
            ],
        "param_name_types": {
            "isi": "scalar",
            "TauRefrac": "scalar",
            "spikeStart": "scalar",
            "duration": "scalar",
           },
    },
    translations = (
        ("rate",       "isi",           partial(rate_to_isi, "rate"),  partial(isi_to_rate, "isi")),
        ("start",      "spikeStart"),
        ("duration",   "duration"),
        ("tau_refrac", "TauRefrac",     partial(ms_to_timesteps, "tau_refrac"), partial(timesteps_to_ms, "TauRefrac"))
    ),
    extra_param_values = {
        "timeStepToSpike" : 0.0,
        "RefracTime" : 0.0
    })

genn_neuron_defs["Gamma"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            oldSpike = false;
            if($(timeStepToSpike) <= 0.0f) {
                $(timeStepToSpike) += $(beta) * $(gennrand_gamma, $(alpha));
            }
            $(timeStepToSpike) -= 1.0;
        """,

        "threshold_condition_code" : "$(t) >= $(start) && $(t) < $(start) + $(duration) && $(timeStepToSpike) <= 0.0",

        "var_name_types": [
            ("timeStepToSpike", "scalar")],

        "param_name_types": {
            "alpha": "scalar",
            "beta": "scalar",
            "start": "scalar",
            "duration": "scalar"},
    },
    translations = (
        ("alpha",       "alpha"),
        ("beta",        "beta",     partial(rate_to_isi, "beta"),  partial(isi_to_rate, "beta")),
        ("start",       "start"),
        ("duration",    "duration")
    ),
    extra_param_values = {
        "timeStepToSpike" : 0.0,
    })

genn_neuron_defs["InhGamma"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            oldSpike = false;
            if ($(t) >= $(spikeStart) && $(t) < $(spikeStart) + $(duration)) {
                if ($(t) > $(tbins)[$(startIndex)] && $(startIndex) != $(endIndex)) {
                    $(startIndex)++;
                    const scalar a= $(alpha)[$(startIndex)];
                    const scalar b= $(beta)[$(startIndex)];
                    $(timeStepToSpike) = $(tbins)[$(startIndex)]+b*$(gennrand_gamma,a);
                }
                if ($(timeStepToSpike) <= 0.0f) {
                    const scalar a= $(alpha)[$(startIndex)];
                    const scalar b= $(beta)[$(startIndex)];
                    $(timeStepToSpike) += b*$(gennrand_gamma,a);
                }
                $(timeStepToSpike) -= 1.0;
            }
        """,

        "threshold_condition_code" : "$(t) >= $(spikeStart) && $(t) < $(spikeStart) + $(duration) && $(timeStepToSpike) <= 0.0",

        "var_name_types" : [
            ("timeStepToSpike", "scalar"),
            ("startIndex", "unsigned int"),
            ("endIndex", "unsigned int")
        ],

        "param_name_types": {
            "spikeStart": "scalar",
            "duration": "scalar",
        },
        
        "extra_global_params": [
            ("alpha", "scalar*"),
            ("tbins", "scalar*"),
            ("beta", "scalar*")
        ]
    },
    translations = (
        ("a",          "alpha"),
        ("tbins",      "tbins"),
        ("b",          "beta"),
        ("start",      "spikeStart"),
        ("duration",   "duration"),
    ),
    extra_param_values = {
        "timeStepToSpike" : 0.0
    })

genn_neuron_defs["Izhikevich"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            if ($(V) >= 30.0){
               $(V)=$(c);
               $(U)+=$(d);
            }
            $(V)+=0.5*(0.04*$(V)*$(V)+5.0*$(V)+140.0-$(U)+$(Isyn)+$(Ioffset))*DT; //at two times for numerical stability
            $(V)+=0.5*(0.04*$(V)*$(V)+5.0*$(V)+140.0-$(U)+$(Isyn)+$(Ioffset))*DT;
            $(U)+=$(a)*($(b)*$(V)-$(U))*DT;
            if ($(V) > 30.0) {
              $(V)=30.0;
            }
        """,

        "threshold_condition_code" : "$(V) >= 29.99",

        "var_name_types" : [
            ("V", "scalar"),
            ("U", "scalar")],
        "param_name_types": {
            "a": "scalar",
            "b": "scalar",
            "c": "scalar",
            "d": "scalar",
            "Ioffset": "scalar"},
    },
    translations = (
        ("a",        "a"),
        ("b",        "b"),
        ("c",        "c"),
        ("d",        "d"),
        ("i_offset", "Ioffset", 1000),
        ("v",        "V"),
        ("u",        "U")
    ),
    extra_param_values = {})

genn_neuron_defs["HH"] = GeNNDefinitions(
    definitions = {
        "sim_code" : """
            scalar Imem;
            unsigned int mt;
            scalar mdt= DT/25.0;
            for (mt=0; mt < 25; mt++) {
               Imem= -($(m)*$(m)*$(m)*$(h)*$(gNa)*($(V)-($(ENa)))+
                   $(n)*$(n)*$(n)*$(n)*$(gK)*($(V)-($(EK)))+
                   $(gl)*($(V)-($(El)))-$(Isyn)-$(Ioffset));
               scalar _a;
               if (lV == -50.0) {
                   _a= 1.28;
               }
               else {
                   _a= 0.32*(-50.0-$(V))/(exp((-50.0-$(V))/4.0)-1.0);
               }
               scalar _b;
               if (lV == -23.0) {
                   _b= 1.4;
               }
               else {
                   _b= 0.28*($(V)+23.0)/(exp(($(V)+23.0)/5.0)-1.0);
               }
               $(m)+= (_a*(1.0-$(m))-_b*$(m))*mdt;
               _a= 0.128*exp((-46.0-$(V))/18.0);
               _b= 4.0 / (exp((-23.0-$(V))/5.0)+1.0);
               $(h)+= (_a*(1.0-$(h))-_b*$(h))*mdt;
               if (lV == -48.0) {
                   _a= 0.16;
               }
               else {
                   _a= 0.032*(-48.0-$(V))/(exp((-48.0-$(V))/5.0)-1.0);
               }
               _b= 0.5*exp((-53.0-$(V))/40.0);
               $(n)+= (_a*(1.0-$(n))-_b*$(n))*mdt;
               $(V)+= Imem/$(C)*mdt;
            }
        """,

        "threshold_condition_code" : "$(V) >= 33.0",

        "var_name_types" : [
            ("V", "scalar"),
            ("m", "scalar"),
            ("h", "scalar"),
            ("n", "scalar")],
        "param_name_types": {
            "gNa": "scalar",
            "ENa": "scalar",
            "gK": "scalar",
            "EK": "scalar",
            "gl": "scalar",
            "El": "scalar",
            "C": "scalar",
            "Ioffset": "scalar"}
    },
    translations = (
        ("gbar_Na",    "gNa"),
        ("gbar_K",     "gK"),
        ("g_leak",     "gl"),
        ("cm",         "C"),
        ("e_rev_Na",   "ENa"),
        ("e_rev_K",    "EK"),
        ("e_rev_leak", "El"),
        ("v",          "V"),
        ("v_offset",   "V_OFFSET"),
        ("i_offset",   "Ioffset"),
    ),
    extra_param_values = {
        "m" : 0.0,
        "h" : 1.0,
        "n" : 0.0
    })

genn_postsyn_defs = {}
genn_postsyn_defs["ExpCurr"] = GeNNDefinitions(
    definitions = {
        "decay_code" : "$(inSyn)*=$(expDecay);",

        "apply_input_code" : "$(Isyn) += $(init) * $(inSyn);",

        "var_name_types" : [],
        "param_name_types" : {
            "expDecay": "scalar",
            "init": "scalar"}
    },
    translations = (
        ("tau_syn_E",  "exc_expDecay",  partial(tau_to_decay, "tau_syn_E"),   None),
        ("tau_syn_I",  "inh_expDecay",  partial(tau_to_decay, "tau_syn_I"),   None),
    ),
    extra_param_values = {
        "exc_init": partial(tau_to_init, "tau_syn_E"),
        "inh_init": partial(tau_to_init, "tau_syn_I")
    })

genn_postsyn_defs["ExpCond"] = GeNNDefinitions(
    definitions = {
        "decay_code" : "$(inSyn)*=$(expDecay);",

        "apply_input_code" : "$(Isyn) += $(init) * $(inSyn) * ($(E) - $(V));",

        "var_name_types" : [],
        "param_name_types" : {
            "expDecay": "scalar",
            "init": "scalar",
            "E": "scalar"}
    },
    translations = (
        ("e_rev_E",    "exc_E"),
        ("e_rev_I",    "inh_E"),
        ("tau_syn_E",  "exc_expDecay",  partial(tau_to_decay, "tau_syn_E"),   None),
        ("tau_syn_I",  "inh_expDecay",  partial(tau_to_decay, "tau_syn_I"),   None)
    ),
    extra_param_values = {
        "exc_init": partial(tau_to_init, "tau_syn_E"),
        "inh_init": partial(tau_to_init, "tau_syn_I")
    })

genn_postsyn_defs["AlphaCurr"] = GeNNDefinitions(
    definitions = {
        "decay_code" : """
            $(x) = exp(-DT/$(tau)) * ((DT * $(inSyn) * exp(1.0f) / $(tau)) + $(x));
            $(inSyn)*=exp(-DT/$(tau));
        """,

        "apply_input_code" : "$(Isyn) += $(x);",

        "var_name_types" : [
            ("x", "scalar")],
        "param_name_types" : {
            "tau": "scalar"}
    },
    translations = (
        ("tau_syn_E",  "exc_tau"),
        ("tau_syn_I",  "inh_tau"),
    ),
    extra_param_values = {
        "exc_x" : 0.0,
        "inh_x" : 0.0,
    })

genn_postsyn_defs["AlphaCond"] = GeNNDefinitions(
    definitions = {
        "decay_code" : """
            $(x) = exp(-DT/$(tau)) * ((DT * $(inSyn) * exp(1.0f) / $(tau)) + $(x));
            $(inSyn)*=exp(-DT/$(tau));
        """,

        "apply_input_code" : "$(Isyn) += ($(E) - $(V)) * $(x);",

        "var_name_types" : [
            ("x", "scalar")],
        "param_name_types" : {
            "tau": "scalar",
            "E": "scalar"}
    },
    translations = (
        ("e_rev_E",    "exc_E"),
        ("e_rev_I",    "inh_E"),
        ("tau_syn_E",  "exc_tau"),
        ("tau_syn_I",  "inh_tau"),
    ),
    extra_param_values = {
        "exc_x" : 0.0,
        "inh_x" : 0.0,
    })

genn_postsyn_defs["DeltaCurr"] = GeNNDefinitions({}, (), True)

class IF_curr_alpha(cells.IF_curr_alpha, GeNNStandardCellType):
    __doc__ = cells.IF_curr_alpha.__doc__

    genn_neuron_name = "IF"
    genn_postsyn_name = "AlphaCurr"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]
    
class IF_curr_exp(cells.IF_curr_exp, GeNNStandardCellType):
    __doc__ = cells.IF_curr_exp.__doc__

    genn_neuron_name = "IF"
    genn_postsyn_name = "ExpCurr"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class IF_cond_alpha(cells.IF_cond_alpha, GeNNStandardCellType):
    __doc__ = cells.IF_cond_alpha.__doc__

    genn_neuron_name = "IF"
    genn_postsyn_name = "AlphaCond"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class IF_cond_exp(cells.IF_cond_exp, GeNNStandardCellType):
    __doc__ = cells.IF_cond_exp.__doc__

    genn_neuron_name = "IF"
    genn_postsyn_name = "ExpCond"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class IF_facets_hardware1(cells.IF_facets_hardware1):
    __doc__ = cells.IF_facets_hardware1.__doc__


class HH_cond_exp(cells.HH_cond_exp, GeNNStandardCellType):
    __doc__ = cells.HH_cond_exp.__doc__

    genn_neuron_name = "HH"
    genn_postsyn_name = "ExpCond"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class IF_cond_exp_gsfa_grr(cells.IF_cond_exp_gsfa_grr, GeNNStandardCellType):
    __doc__ = cells.IF_cond_exp_gsfa_grr.__doc__

    genn_neuron_name = "Adapt"
    genn_postsyn_name = "ExpCond"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class SpikeSourcePoisson(cells.SpikeSourcePoisson, GeNNStandardCellType):
    __doc__ = cells.SpikeSourcePoisson.__doc__

    genn_neuron_name = "Poisson"
    neuron_defs = genn_neuron_defs[genn_neuron_name]

class SpikeSourcePoissonRefractory(cells.SpikeSourcePoissonRefractory, GeNNStandardCellType):
    __doc__ = cells.SpikeSourcePoissonRefractory.__doc__

    genn_neuron_name = "PoissonRef"
    neuron_defs = genn_neuron_defs[genn_neuron_name]

class SpikeSourceArray(cells.SpikeSourceArray, GeNNStandardCellType):
    __doc__ = cells.SpikeSourceArray.__doc__
    genn_neuron_name = "SpikeSourceArray"
    neuron_defs = GeNNDefinitions(
        definitions = {
            "sim_code": "oldSpike = false;\n",
            "threshold_condition_code": "$(startSpike) != $(endSpike) && $(t) >= $(spikeTimes)[$(startSpike)]",
            "reset_code": "$(startSpike)++;\n",

            "var_name_types": [("startSpike", "unsigned int"), ("endSpike", "unsigned int")],
            "extra_global_params": [("spikeTimes", "scalar*")]
        },
        translations = (
            ("spike_times", "spikeTimes"),
        ),
        extra_param_values = {})

    def get_extra_global_neuron_params(self, native_params, init_vals):
        # Get spike times
        spk_times = native_params["spikeTimes"]

        # Concatenate together spike times to form extra global parameter
        return {"spikeTimes" : np.concatenate([seq.value
                                               for seq in spk_times])}

    def build_genn_neuron(self, native_params, init_vals):
        # Create model using unmodified defs
        genn_model = create_custom_neuron_class(self.genn_neuron_name,
                                                **self.neuron_defs.definitions)()

        # Get spike times
        spk_times = native_params["spikeTimes"]

        # Create empty numpy arrays to hold start and end spikes indices
        start_spike = np.empty(shape=native_params.shape, dtype=np.uint32)
        end_spike = np.empty(shape=native_params.shape, dtype=np.uint32)

        # Calculate indices for each sequence
        cum_size = 0
        for i, seq in enumerate(spk_times):
            start_spike[i] = cum_size
            cum_size += len(seq.value)
            end_spike[i] = cum_size

        # Build initialisation dictionary
        neuron_ini = {"startSpike": start_spike,
                      "endSpike": end_spike}

        # Return with model
        return genn_model, [], neuron_ini

class SpikeSourceGamma(cells.SpikeSourceGamma, GeNNStandardCellType):
    __doc__ = cells.SpikeSourceGamma

    genn_neuron_name = "Gamma"
    neuron_defs = genn_neuron_defs[genn_neuron_name]

class SpikeSourceInhGamma(cells.SpikeSourceInhGamma, GeNNStandardCellType):
    __doc__ = cells.SpikeSourceInhGamma.__doc__
    genn_neuron_name = "InhGamma"
    neuron_defs = genn_neuron_defs[genn_neuron_name]

    def get_extra_global_neuron_params(self, native_params, init_vals):
        # Get alpha, tbins and beta
        alpha_val = native_params["alpha"]
        tbin_val = native_params["tbins"]
        beta_val = native_params["beta"]

        # Concatenate together a, tbin ans b to form extra global parameter
        return {"alpha" : np.concatenate([seq.value for seq in alpha_val]),
                "tbins" : np.concatenate([seq.value for seq in tbin_val]),
                "beta" : np.concatenate([1000.0 / (seq.value * state.dt) 
                                         for seq in beta_val])}

    def build_genn_neuron(self, native_params, init_vals):
        # Take a copy of the native parameters
        amended_native_params = deepcopy(native_params)

        # Create empty numpy arrays to hold start and end step indices
        start_index = np.empty(shape=amended_native_params.shape, dtype=np.uint32)
        end_index = np.empty(shape=amended_native_params.shape, dtype=np.uint32)

        # Calculate indices for each sequence
        cum_size = 0
        for i, seq in enumerate(native_params["tbins"]):
            start_index[i] = cum_size
            cum_size += len(seq.value)
            end_index[i] = cum_size

        # Wrap indices in lazy arrays and add to amended native parameters
        amended_native_params["startIndex"] = la.larray(start_index)
        amended_native_params["endIndex"] = la.larray(end_index)

        # Call superclass method to build 
        # neuron model from amended native parameters
        return super(SpikeSourceInhGamma, self).build_genn_neuron(
            amended_native_params, init_vals)


class EIF_cond_alpha_isfa_ista(cells.EIF_cond_alpha_isfa_ista, GeNNStandardCellType):
    __doc__ = cells.EIF_cond_alpha_isfa_ista.__doc__
    genn_neuron_name = "AdExp"
    genn_postsyn_name = "AlphaCond"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class EIF_cond_exp_isfa_ista(cells.EIF_cond_exp_isfa_ista, GeNNStandardCellType):
    __doc__ = cells.EIF_cond_exp_isfa_ista.__doc__
    genn_neuron_name = "AdExp"
    genn_postsyn_name = "ExpCond"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

class Izhikevich(cells.Izhikevich, GeNNStandardCellType):
    __doc__ = cells.Izhikevich.__doc__
    genn_neuron_name = "Izhikevich"
    genn_postsyn_name = "DeltaCurr"
    neuron_defs = genn_neuron_defs[genn_neuron_name]
    postsyn_defs = genn_postsyn_defs[genn_postsyn_name]

    standard_receptor_type = True
    receptor_scale = 1e-3  # synaptic weight is in mV, so need to undo usual weight scaling

