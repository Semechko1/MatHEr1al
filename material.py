import xml.etree.ElementTree as ET
import os.path
from IEEE754_to_float import ieee754_to_float as iee754

def read_string(start, file):
    file.seek(start)
    name=""
    temp_chara=""
    while True:
        if temp_chara != "00":
            name = name + temp_chara
            temp_chara = file.read(1).hex()
        else:
            break
    name = bytes.fromhex(name).decode()
    return name

def read_param(start, Parameters, mat_file, offset):
    mat_file.seek(start+offset)
    node = int(mat_file.read(4).hex(), 16) #00000100
    par_name_st = int(mat_file.read(4).hex(), 16) #add root_node_offset
    par_loc_st = int(mat_file.read(4).hex(), 16) #add root_node_offset
    par_name = read_string(par_name_st+offset, mat_file) #gets parameter name
    mat_file.seek(par_loc_st+offset)
    Parameter = ET.SubElement(Parameters, par_name)
    ET.SubElement(Parameter, "value_W").text = str(round(iee754(mat_file.read(4).hex()), 5))
    ET.SubElement(Parameter, "value_X").text = str(round(iee754(mat_file.read(4).hex()), 5))
    ET.SubElement(Parameter, "value_Y").text = str(round(iee754(mat_file.read(4).hex()), 5))
    ET.SubElement(Parameter, "value_Z").text = str(round(iee754(mat_file.read(4).hex()), 5))

def open_texture(file_path, folder_path):
    try:
        texture = open(f'{folder_path}/{file_path}.texture','rb')

        texture_fsize = int(texture.read(4).hex(), 16)
        texture_version = int(texture.read(4).hex(), 16)  # 00000000
        texture_offset_final_table = int(texture.read(4).hex(), 16)
        texture_root_node_offset = int(texture.read(4).hex(), 16)
        texture_offset_final_table_abs = int(texture.read(4).hex(), 16)

        texture_padding1 = int(texture.read(4).hex(), 16) # 00000000
        texture_fname_l = int(texture.read(4).hex(), 16)
        texture_padding1 = int(texture.read(4).hex(), 16)  # 00000000
        texture_type_l = int(texture.read(4).hex(), 16)
        return (read_string(texture_fname_l+texture_root_node_offset, texture),
                read_string(texture_type_l+texture_root_node_offset, texture))
    except FileNotFoundError:
        print(f"couldn't find texture: {folder_path}/{file_path}.texture")
        return ("Missing_texture","None")

def open_texset(file_path, xml_tree, folder_path):
    try:
        texset = open(f'{folder_path}/{file_path}.texset', 'rb')

        texset_fsize = int(texset.read(4).hex(), 16)
        texset_version = int(texset.read(4).hex(), 16)  # 00000000
        texset_offset_final_table = int(texset.read(4).hex(), 16)
        texset_root_node_offset = int(texset.read(4).hex(), 16)
        texset_offset_final_table_abs = int(texset.read(4).hex(), 16)

        texset_padding = int(texset.read(4).hex(), 16)  # 00000000
        texset_amnt_textures = int(texset.read(4).hex(), 16)
        texset_locats_start = int(texset.read(4).hex(), 16)  # usually 00000008
        Textures = ET.SubElement(xml_tree, "Textures")
        for i in range(texset_amnt_textures):
            cur_texture_name = str(read_string(int(texset.read(4).hex(), 16) + texset_root_node_offset, texset))
            texset.seek(texset_locats_start + texset_root_node_offset + 4 * (i + 1))
            texture_file, texture_type = open_texture(cur_texture_name, folder_path)
            if texture_file == "Missing_texture":
                ET.SubElement(Textures, "Missing_texture")
            else:
                Texture = ET.SubElement(Textures, "texture")
                ET.SubElement(Texture, "name").text = cur_texture_name
                ET.SubElement(Texture, "texture_file").text = str(texture_file)
                ET.SubElement(Texture, "texture_type").text = str(texture_type)
    except FileNotFoundError:
        print(f"couldn't found texset: '{folder_path}/{file_path}.texset")
        ET.SubElement(xml_tree, "No_texset_available")



def convert_mat_to_xml (input_file):
    mat_file = open(input_file, 'rb')

    root = ET.Element("Material")

    #header
    fsize = int(mat_file.read(4).hex(), 16)
    version = int(mat_file.read(4).hex(), 16)
    ET.SubElement(root, "version").text = str(version)
    offset_final_table = int(mat_file.read(4).hex(), 16)
    root_node_offset = int(mat_file.read(4).hex(), 16) #usually 24
    offset_final_table_abs = int(mat_file.read(4).hex(), 16)
    padding = int(mat_file.read(4).hex(), 16)
    #after_header
    shader_location1 = int(mat_file.read(4).hex(), 16)
    shader_location2 = int(mat_file.read(4).hex(), 16)
    mat_name_loc = int(mat_file.read(4).hex(), 16)
    unknown1 = int(mat_file.read(4).hex(), 16) #zeroes

    alpha_threshold = int(mat_file.read(1).hex(), 16) #80
    two_sided = int(mat_file.read(1).hex(), 16) #00/01
    additive = int(mat_file.read(1).hex(), 16) #00/01
    unknown2 = int(mat_file.read(1).hex(), 16) #80
    ET.SubElement(root, "Alpha_threshold").text = str(alpha_threshold)
    ET.SubElement(root, "Two_sided").text = str(two_sided)
    ET.SubElement(root, "Additive").text = str(additive)

    amount_of_params = int(mat_file.read(1).hex(), 16) #06
    unknown3 = int(mat_file.read(3).hex(), 16) #000000
    parameters_start = int(mat_file.read(4).hex(), 16) #
    unknown5 = int(mat_file.read(4).hex(), 16) #zeroes
    unknown6 = int(mat_file.read(4).hex(), 16) #zeroes

    shader_name1 = read_string(shader_location1+root_node_offset, mat_file)
    ET.SubElement(root, "Shader").text = shader_name1
    shader_name2 = read_string(shader_location2+root_node_offset, mat_file)
    mat_name = read_string(mat_name_loc+root_node_offset, mat_file)
    ET.SubElement(root, "Material_Name").text = mat_name #could actualy be texset name

    mat_file.seek(parameters_start+root_node_offset)
    pos = mat_file.tell()
    #print(amount_of_params)
    Parameters = ET.SubElement(root, "Parameters")
    for i in range(amount_of_params):
        read_param(int(mat_file.read(4).hex(), 16), Parameters, mat_file, root_node_offset)
        mat_file.seek(pos+4*(i+1))

    #print(input_file, os.path.split(input_file)[1])
    open_texset(mat_name, root, os.path.split(input_file)[0])

    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(f"{os.path.split(input_file)[0]}/{os.path.split(input_file)[1].split('.')[0]}.xml")

convert_mat_to_xml("./te.st/chains.material")
