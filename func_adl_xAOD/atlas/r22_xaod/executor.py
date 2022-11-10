from func_adl_xAOD.atlas.xaod.executor import atlas_xaod_executor


class atlas_r22_xaod_executor(atlas_xaod_executor):
    def __init__(self, template_dir_name="func_adl_xAOD/template/atlas/r22"):
        super().__init__(template_dir_name)
