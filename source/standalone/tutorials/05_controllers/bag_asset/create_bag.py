import os
from omni.physx.scripts import physicsUtils, particleUtils
import omni.isaac.core.utils.prims as prim_utils
from pxr import UsdGeom, UsdPhysics, Gf, Sdf, UsdShade
import omni


def create_bag(scene):
    
    stage = scene.stage

    #adding a bag model
    bag_pos = (0.57, -0.27, 0.18)
    bag_path = "/World/envs/env_0/Bag"
    bag_mesh_path = bag_path + "/bag0_28/Cube_0_1_021_Cube_136"
    bag_file_path = os.path.dirname(__file__) + "/bag.usd"
    prim_utils.create_prim(bag_path, usd_path =bag_file_path, translation=bag_pos, orientation = (0.707, 0.707, 0, 0), scale =(0.1, 0.1, 0.1))
    
    # configure and create particle system
    particle_system_path = bag_path + "/particleSystem"
    particle_material_path = bag_path + "/particleMaterial"

    # size rest offset according to plane resolution and width so that particles are just touching at rest
    radius = 0.005 #0.002 # * (plane_width / plane_resolution)
    restOffset = radius
    contactOffset = restOffset * 1.5
    particleUtils.add_physx_particle_system(
        stage=stage,
        particle_system_path=particle_system_path,
        contact_offset=contactOffset,
        rest_offset=restOffset,
        particle_contact_offset=contactOffset,
        solid_rest_offset=restOffset,
        fluid_rest_offset=0.0,
        enable_ccd=True,
        solver_position_iterations=48,
        simulation_owner = scene.physics_scene_path
        #world.get_physics_context().prim_path,
    )

    # create material and assign it to the system:
    # add some drag and lift to get aerodynamic effects
    particleUtils.add_pbd_particle_material(stage, particle_material_path, drag=0.0001, lift=0.0001, friction=0.6)
    physicsUtils.add_physics_material_to_prim(
        stage, stage.GetPrimAtPath(particle_system_path), particle_material_path
    )
    
    #configure as cloth
    stretchStiffness = 100000.0 #50000.0
    bendStiffness = 500.0 #10
    shearStiffness = 200.0 #5
    damping = 1.3
       
    particleUtils.add_physx_particle_cloth(
        stage=stage,
        path=bag_mesh_path,
        dynamic_mesh_path=None,
        particle_system_path=particle_system_path,
        spring_stretch_stiffness=stretchStiffness,
        spring_bend_stiffness=bendStiffness,
        spring_shear_stiffness=shearStiffness,
        spring_damping=damping,
        self_collision=True,
        self_collision_filter=True,
    )
    
    # configure mass:
    particle_mass = 0.0001
    bag_mesh = UsdGeom.Mesh(stage.GetPrimAtPath(bag_mesh_path))
    num_verts = len(UsdGeom.Mesh(bag_mesh).GetPointsAttr().Get())
    mass = 0.020 #particle_mass * num_verts
    massApi = UsdPhysics.MassAPI.Apply(bag_mesh.GetPrim())
    massApi.GetMassAttr().Set(mass)

    # add render material:
    target_path = "/World/envs/env_0/Looks/OmniPBR"
    material_path = create_pbd_material(stage,target_path,"OmniPBR")

    omni.kit.commands.execute(
        "BindMaterialCommand", prim_path=bag_mesh_path, material_path=material_path, strength=None
    )


def create_pbd_material(stage, target_path: str, mat_name: str, color_rgb: Gf.Vec3f = Gf.Vec3f(0.2, 0.2, 0.8)) -> Sdf.Path:
        # create material for extras
        create_list = []

        omni.kit.commands.execute(
            "CreateAndBindMdlMaterialFromLibrary",
            mdl_name="OmniPBR.mdl",
            mtl_name="OmniPBR",
            mtl_created_list=create_list,
            bind_selected_prims=False,
        )
        if create_list[0] != target_path:
            omni.kit.commands.execute("MovePrims", paths_to_move={create_list[0]: target_path})
        shader = UsdShade.Shader.Get(stage, target_path + "/Shader")
        shader.CreateInput("diffuse_color_constant", Sdf.ValueTypeNames.Color3f).Set(color_rgb)
        return Sdf.Path(target_path)

