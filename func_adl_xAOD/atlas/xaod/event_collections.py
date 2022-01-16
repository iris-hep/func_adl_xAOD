from typing import Union
import func_adl_xAOD.common.cpp_types as ctyp
from func_adl_xAOD.common.event_collections import (
    EventCollectionSpecification, event_collection_coder,
    event_collection_collection_container, event_collection_container)


class atlas_xaod_event_collection_container(event_collection_container):
    def __init__(self, type_name: Union[str, ctyp.CPPParsedTypeInfo], p_depth: int = 1):
        super().__init__(type_name, p_depth=p_depth)

    def __str__(self):
        return f"const {self.type} *"


class atlas_xaod_event_collection_collection(event_collection_collection_container):
    def __init__(self, type_name: Union[str, ctyp.CPPParsedTypeInfo],
                 element_name: Union[str, ctyp.CPPParsedTypeInfo],
                 p_depth_type: int = 1, p_depth_element: int = 1):
        super().__init__(type_name, element_name, p_depth_element=p_depth_element, p_depth_type=p_depth_type)

    def __str__(self):
        return f"const {self.type}*"


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
atlas_xaod_collections = [
    EventCollectionSpecification('atlas', 'Jets',
                                 ['xAODJet/JetContainer.h'],
                                 atlas_xaod_event_collection_collection('xAOD::JetContainer', 'xAOD::Jet'),
                                 ['xAODJet'],
                                 ),
    EventCollectionSpecification('atlas', 'Tracks',
                                 ['xAODTracking/TrackParticleContainer.h'],
                                 atlas_xaod_event_collection_collection('xAOD::TrackParticleContainer', 'xAOD::TrackParticle'),
                                 ['xAODTracking'],
                                 ),
    EventCollectionSpecification('atlas', 'EventInfo',
                                 ['xAODEventInfo/EventInfo.h'],
                                 atlas_xaod_event_collection_container('xAOD::EventInfo'),
                                 ['xAODEventInfo'],
                                 ),
    EventCollectionSpecification('atlas', 'TruthParticles',
                                 ['xAODTruth/TruthParticleContainer.h', 'xAODTruth/TruthParticle.h', 'xAODTruth/TruthVertex.h'],
                                 atlas_xaod_event_collection_collection('xAOD::TruthParticleContainer', 'xAOD::TruthParticle'),
                                 ['xAODTruth'],
                                 ),
    EventCollectionSpecification('atlas', 'Electrons',
                                 ['xAODEgamma/ElectronContainer.h', 'xAODEgamma/Electron.h'],
                                 atlas_xaod_event_collection_collection('xAOD::ElectronContainer', 'xAOD::Electron'),
                                 ['xAODEgamma'],
                                 ),
    EventCollectionSpecification('atlas', 'Muons',
                                 ['xAODMuon/MuonContainer.h', 'xAODMuon/Muon.h'],
                                 atlas_xaod_event_collection_collection('xAOD::MuonContainer', 'xAOD::Muon'),
                                 ['xAODMuon'],
                                 ),
    EventCollectionSpecification('atlas', 'MissingET',
                                 ['xAODMissingET/MissingETContainer.h', 'xAODMissingET/MissingET.h'],
                                 atlas_xaod_event_collection_collection('xAOD::MissingETContainer', 'xAOD::MissingET'),
                                 ['xAODMissingET'],
                                 ),
]


def define_default_atlas_types():
    'Define the default atlas types'
    ctyp.add_method_type_info("xAOD::TruthParticle", "prodVtx", ctyp.terminal('xAODTruth::TruthVertex', p_depth=1))
    ctyp.add_method_type_info("xAOD::TruthParticle", "decayVtx", ctyp.terminal('xAODTruth::TruthVertex', p_depth=1))
    ctyp.add_method_type_info("xAOD::TruthParticle", "parent", ctyp.terminal('xAOD::TruthParticle', p_depth=1))
    ctyp.add_method_type_info("xAOD::TruthParticle", "child", ctyp.terminal('xAOD::TruthParticle', p_depth=1))


class atlas_event_collection_coder(event_collection_coder):
    def get_running_code(self, container_type: event_collection_container) -> list:
        return [f'{container_type} result = 0;',
                'ANA_CHECK (evtStore()->retrieve(result, collection_name));']
