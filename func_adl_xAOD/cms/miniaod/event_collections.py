from typing import Union

import func_adl_xAOD.common.cpp_types as ctyp
import func_adl_xAOD.common.cpp_ast as cpp_ast
import func_adl_xAOD.common.cpp_representation as crep
from func_adl_xAOD.common.cpp_vars import unique_name
from func_adl_xAOD.common.util_scope import gc_scope_top_level
from func_adl_xAOD.common.event_collections import (
    EventCollectionSpecification, event_collection_coder, event_collection_collection_container, event_collection_container)


# There is no use for a CMS single item collection - everything they have
# has multiple items in it. Copy from the ATLAS example to get this working correctly.


class cms_miniaod_event_collection_collection(event_collection_collection_container):
    def __init__(self, type_name: Union[str, ctyp.CPPParsedTypeInfo],
                 element_name: Union[str, ctyp.CPPParsedTypeInfo],
                 p_depth_type: int = 1, p_depth_element: int = 0):
        super().__init__(type_name, element_name, p_depth_element=p_depth_element, p_depth_type=p_depth_type)

    def __str__(self):
        return f"Handle<{self.type}>"

    def token_type(self):
        # Return the type of the token. This token can be used to get data via
        # functions like getByToken()
        return f"edm::EDGetTokenT<{self.type}>"


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
cms_miniaod_collections = [
    EventCollectionSpecification('cms_miniaod', "Muons",
                                 ["DataFormats/PatCandidates/interface/Muon.h"
                                  ],
                                 cms_miniaod_event_collection_collection('pat::MuonCollection', 'pat::Muon'),
                                 [],
                                 ),
    EventCollectionSpecification('cms_miniaod', "Vertex",
                                 ["DataFormats/VertexReco/interface/Vertex.h",
                                  "DataFormats/VertexReco/interface/VertexFwd.h"
                                  ],
                                 cms_miniaod_event_collection_collection('reco::VertexCollection', 'reco::Vertex', p_depth_element=0),
                                 [],
                                 ),
    EventCollectionSpecification('cms_miniaod', "Electrons",
                                 ['DataFormats/PatCandidates/interface/Electron.h',
                                  'DataFormats/EgammaCandidates/interface/GsfElectron.h'
                                  ],
                                 cms_miniaod_event_collection_collection('pat::ElectronCollection', 'pat::Electron'),
                                 [],
                                 ),
]


def define_default_cms_types():
    'Define the default cms types'
    ctyp.add_method_type_info("reco::TrackRef", "hitPattern", ctyp.terminal('reco::HitPattern'))

    ctyp.add_method_type_info("pat::Muon", "globalTrack", ctyp.terminal('reco::TrackRef', p_depth=1))
    ctyp.add_method_type_info("pat::Muon", "isPFIsolationValid", ctyp.terminal('bool'))
    ctyp.add_method_type_info("pat::Muon", "isPFMuon", ctyp.terminal('bool'))
    ctyp.add_method_type_info("pat::Muon", "pfIsolationR04", ctyp.terminal('reco::MuonPFIsolation'))

    ctyp.add_method_type_info("pat::Electron", "gsfTrack", ctyp.terminal('reco::GsfTrackRef', p_depth=1))
    ctyp.add_method_type_info("pat::Electron", "isEB", ctyp.terminal('bool'))
    ctyp.add_method_type_info("pat::Electron", "isEE", ctyp.terminal('bool'))
    ctyp.add_method_type_info("pat::Electron", "passingPflowPreselection", ctyp.terminal('bool'))
    ctyp.add_method_type_info("pat::Electron", "superCluster", ctyp.terminal('reco::SuperClusterRef', p_depth=1))
    ctyp.add_method_type_info("pat::Electron", "pfIsolationVariables", ctyp.terminal('reco::GsfElectron::PflowIsolationVariables'))

    ctyp.add_method_type_info("reco::GsfTrack", "trackerExpectedHitsInner", ctyp.terminal('reco::HitPattern'))  # reco::HitPattern is the expected return type


class cms_event_collection_coder(event_collection_coder):
    t_name = unique_name("token")

    def get_running_code(self, container_type: event_collection_container) -> list:
        return [f'{container_type} result;',
                f'iEvent.getByToken({self.t_name}, result);']

    def get_running_code_CPPCodeValue(self, cpv: cpp_ast.CPPCodeValue, md: EventCollectionSpecification):
        # Used to build CPPCodeVlue for miniAOD
        cpv.running_code = self.get_running_code(md.container_type)
        # Specify the token name and type
        token_variable = crep.cpp_variable(self.t_name, gc_scope_top_level, ctyp.terminal(md.container_type.token_type()))
        # value of initializing the token
        token_init = f'consumes<{md.container_type.type}>(edm::InputTag(collection_name))'
        # add both token declaration and initializtion to CPPCodeValue.fields for building the cpp files
        cpv.fields.append((token_variable, token_init))
