import os.path
import struct
import sys
import xml.etree.ElementTree as ET
from IEEE754_to_float import ieee754_to_float as iee754

def go_back_and_write(file, location, mtype, value):
    temp_val = file.tell()
    file.seek(location)
    file.write(struct.pack(mtype,value))
    file.seek(temp_val)

def fill_in_zeroes(file, length_of_my_strings):
    if length_of_my_strings % 4!=0:
        for i in range(4-length_of_my_strings%4):
            file.write(b"\x00")

def write_header(file, version):
    file.write(struct.pack('>I', 0))
    file.write(struct.pack('>I', version))  # version = 1
    offset_final_table = file.tell()
    file.write(struct.pack('>I', 0))  # offset to final table without 24
    file.write(struct.pack('>I', 24))  # global offset (usual stuff)
    offset_final_table_abs = file.tell()
    file.write(struct.pack('>I', 0))  # offset to final table with 24
    file.write(struct.pack('>i', 0))  # padding
    # end of header
    return offset_final_table, offset_final_table_abs

def write_footer(file, pointers_locations, offset_final_table, offset_final_table_abs):
    go_back_and_write(file, offset_final_table, '>I', file.tell() - 24)
    go_back_and_write(file, offset_final_table_abs, '>I', file.tell())
    file.write(struct.pack('>I', len(pointers_locations)))
    for pointer in pointers_locations:
        file.write(struct.pack('>I', pointer))
    file.write(struct.pack('>I', 0))  # padding?
    go_back_and_write(file, 0, '>I', file.tell())

def write_texture(filepath, texture_list, tex_amount, indexes_list):
    for i in range(tex_amount):
        texture_file = open(f"{os.path.split(filepath)[0] or '.'}/{texture_list[indexes_list[i]][0]}.texture", 'wb')
        texture_pointers_locations = []

        texture_offset_final_table, texture_offset_final_table_abs = write_header(texture_file,1)
        #header

        pointer_to_fname = texture_file.tell()
        texture_pointers_locations.append(pointer_to_fname-24)
        texture_file.write(struct.pack('>I',0))

        texture_file.write(struct.pack('>b',0)) #free space?
        texture_file.write(struct.pack('>B',int(texture_list[indexes_list[i]][1]))) #U wrap
        texture_file.write(struct.pack('>B', int(texture_list[indexes_list[i]][2]))) #V wrap
        texture_file.write(struct.pack('>b', 0))  # free space?

        pointer_to_ttype = texture_file.tell()
        texture_pointers_locations.append(pointer_to_ttype-24)
        texture_file.write(struct.pack('>I',0))
        fname = str(texture_list[indexes_list[i]][3]).encode('utf-8')+b'\x00'
        ttype = str(texture_list[indexes_list[i]][4]).encode('utf-8')+b'\x00'
        go_back_and_write(texture_file, pointer_to_fname, '>I', texture_file.tell() - 24)
        texture_file.write(fname)
        go_back_and_write(texture_file, pointer_to_ttype, '>I', texture_file.tell() - 24)
        texture_file.write(ttype)
        fill_in_zeroes(texture_file,len(fname+ttype))
        #end of data

        write_footer(texture_file,texture_pointers_locations,texture_offset_final_table, texture_offset_final_table_abs)
        texture_file.close()


def write_texset(filepath, texture_list):
    texset_file = open(f"{os.path.split(filepath)[0] or '.'}/{os.path.split(filepath)[1].split('.')[0]}.texset", 'wb')
    texset_pointers_locations = []

    texset_offset_final_table, texset_offset_final_table_abs = write_header(texset_file, 0)
    #header

    tex_amount = 0
    indexes_list = []
    for i in range(len(texture_list)):
        if texture_list[i]!=[]:
            tex_amount+=1
            indexes_list.append(i)
    texset_file.write(struct.pack('>I',tex_amount))
    pointer_to_name_list=texset_file.tell()
    texset_pointers_locations.append(pointer_to_name_list-24)
    texset_file.write(struct.pack('>I',0)) #location of pointers list
    go_back_and_write(texset_file,pointer_to_name_list,'>I',texset_file.tell()-24)
    for i in range(tex_amount):
        texset_pointers_locations.append(texset_file.tell()-24)
        texset_file.write(struct.pack('>I',0)) #location of texture's name
    length_of_my_strings = 0
    for i in range(tex_amount):
        go_back_and_write(texset_file,texset_pointers_locations[i+1]+24,'>I',texset_file.tell()-24)
        texset_file.write(str(texture_list[indexes_list[i]][0]).encode('utf-8') + b'\x00')
        length_of_my_strings+=len(str(texture_list[indexes_list[i]][0]).encode('utf-8') + b'\x00')
    fill_in_zeroes(texset_file,length_of_my_strings)
    #end of data

    write_footer(texset_file,texset_pointers_locations,texset_offset_final_table, texset_offset_final_table_abs)
    texset_file.close()
    write_texture(filepath,texture_list, tex_amount, indexes_list)


def write_v3_data(mat_file, root, location_list, parameter_list, texture_list, base, pointers_locations):
    shader_ptr_loc = mat_file.tell()
    pointers_locations.append(shader_ptr_loc - base)
    mat_file.write(struct.pack('>I', 0))
    sub_shader_ptr_loc = mat_file.tell()
    pointers_locations.append(sub_shader_ptr_loc - base)
    mat_file.write(struct.pack('>I', 0))
    texset_list_ptr_loc = mat_file.tell()
    pointers_locations.append(texset_list_ptr_loc - base)
    mat_file.write(struct.pack('>I', 0))
    texture_list_ptr_loc = mat_file.tell()
    pointers_locations.append(texture_list_ptr_loc - base)
    mat_file.write(struct.pack('>I', 0))
    mat_file.write(struct.pack('>B', int(root[location_list[2]].text)))
    mat_file.write(struct.pack('>B', int(root[location_list[3]].text)))
    mat_file.write(struct.pack('>B', int(root[location_list[4]].text)))
    mat_file.write(struct.pack('>B', 0))
    tex_indexes = [i for i in range(len(texture_list)) if texture_list[i] != []]
    tex_count = len(tex_indexes)
    param_count = len(parameter_list)
    mat_file.write(struct.pack('>B', param_count))
    mat_file.write(struct.pack('>B', 0))
    mat_file.write(struct.pack('>B', 0))
    mat_file.write(struct.pack('>B', tex_count))
    params_ptr_loc = mat_file.tell()
    pointers_locations.append(params_ptr_loc - base)
    mat_file.write(struct.pack('>I', 0))
    mat_file.write(struct.pack('>I', 0))
    mat_file.write(struct.pack('>I', 0))
    shader_str = str(root[location_list[5]].text).encode('utf-8') + b'\x00'
    go_back_and_write(mat_file, shader_ptr_loc, '>I', mat_file.tell() - base)
    mat_file.write(shader_str)
    go_back_and_write(mat_file, sub_shader_ptr_loc, '>I', mat_file.tell() - base)
    mat_file.write(shader_str)
    fill_in_zeroes(mat_file, len(shader_str) * 2)
    go_back_and_write(mat_file, params_ptr_loc, '>I', mat_file.tell() - base)
    param_ptr_locs = []
    for i in range(param_count):
        param_ptr_locs.append(mat_file.tell())
        pointers_locations.append(mat_file.tell() - base)
        mat_file.write(struct.pack('>I', 0))
    for i in range(param_count):
        go_back_and_write(mat_file, param_ptr_locs[i], '>I', mat_file.tell() - base)
        mat_file.write(b'\x00\x00\x01\x00')
        name_ptr_loc = mat_file.tell()
        pointers_locations.append(name_ptr_loc - base)
        mat_file.write(struct.pack('>I', 0))
        val_ptr_loc = mat_file.tell()
        pointers_locations.append(val_ptr_loc - base)
        mat_file.write(struct.pack('>I', 0))
        name = str(root[location_list[7]][i].tag).encode('utf-8') + b'\x00'
        go_back_and_write(mat_file, name_ptr_loc, '>I', mat_file.tell() - base)
        mat_file.write(name)
        fill_in_zeroes(mat_file, len(name))
        go_back_and_write(mat_file, val_ptr_loc, '>I', mat_file.tell() - base)
        for child in root[location_list[7]][i]:
            mat_file.write(struct.pack('>f', float(child.text)))
    if tex_count > 0:
        go_back_and_write(mat_file, texset_list_ptr_loc, '>I', mat_file.tell() - base)
        unit_name_ptr_locs = []
        for i in tex_indexes:
            unit_name_ptr_locs.append(mat_file.tell())
            pointers_locations.append(mat_file.tell() - base)
            mat_file.write(struct.pack('>I', 0))
        str_total = 0
        for idx, i in enumerate(tex_indexes):
            go_back_and_write(mat_file, unit_name_ptr_locs[idx], '>I', mat_file.tell() - base)
            s = texture_list[i][0].encode('utf-8') + b'\x00'
            mat_file.write(s)
            str_total += len(s)
        fill_in_zeroes(mat_file, str_total)
        go_back_and_write(mat_file, texture_list_ptr_loc, '>I', mat_file.tell() - base)
        tex_struct_ptr_locs = []
        for i in tex_indexes:
            tex_struct_ptr_locs.append(mat_file.tell())
            pointers_locations.append(mat_file.tell() - base)
            mat_file.write(struct.pack('>I', 0))
        for idx, i in enumerate(tex_indexes):
            go_back_and_write(mat_file, tex_struct_ptr_locs[idx], '>I', mat_file.tell() - base)
            fname_ptr_loc2 = mat_file.tell()
            pointers_locations.append(fname_ptr_loc2 - base)
            mat_file.write(struct.pack('>I', 0))
            mat_file.write(struct.pack('>I', (int(texture_list[i][1]) << 16) | (int(texture_list[i][2]) << 8)))
            type_ptr_loc2 = mat_file.tell()
            pointers_locations.append(type_ptr_loc2 - base)
            mat_file.write(struct.pack('>I', 0))
            fname_s = texture_list[i][3].encode('utf-8') + b'\x00'
            go_back_and_write(mat_file, fname_ptr_loc2, '>I', mat_file.tell() - base)
            mat_file.write(fname_s)
            type_s = texture_list[i][4].encode('utf-8') + b'\x00'
            go_back_and_write(mat_file, type_ptr_loc2, '>I', mat_file.tell() - base)
            mat_file.write(type_s)
            fill_in_zeroes(mat_file, len(fname_s) + len(type_s))


def write_material_v1(root, filepath, location_list, parameter_list, texture_list):
    material_file = open(f"{os.path.split(filepath)[0] or '.'}/{os.path.split(filepath)[1].split('.')[0]}.material", 'wb')
    pointers_locations = []
    offset_final_table, offset_final_table_abs = write_header(material_file, int(root[location_list[0]].text))
    shader_location1 = material_file.tell()
    pointers_locations.append(shader_location1 - 24)
    material_file.write(struct.pack('>I', 0))
    shader_location2 = material_file.tell()
    pointers_locations.append(shader_location2 - 24)
    material_file.write(struct.pack('>I', 0))
    material_name_location = material_file.tell()
    pointers_locations.append(material_name_location - 24)
    material_file.write(struct.pack('>I', 0))
    pointers_locations.append(material_file.tell() - 24)
    material_file.write(struct.pack('>i', 0))
    material_file.write(struct.pack('>B', int(root[location_list[2]].text)))
    material_file.write(struct.pack('>B', int(root[location_list[3]].text)))
    material_file.write(struct.pack('>B', int(root[location_list[4]].text)))
    material_file.write(struct.pack('>B', 0))
    material_file.write(struct.pack('<I', int(len(parameter_list))))
    point_to_parameter_list = material_file.tell()
    pointers_locations.append(point_to_parameter_list - 24)
    material_file.write(struct.pack('>I', 0))
    material_file.write(struct.pack('>i', 0))
    material_file.write(struct.pack('>i', 0))
    go_back_and_write(material_file, shader_location1, '>I', material_file.tell() - 24)
    material_file.write(str(root[location_list[5]].text).encode('utf-8') + b'\x00')
    go_back_and_write(material_file, shader_location2, '>I', material_file.tell() - 24)
    material_file.write(str(root[location_list[5]].text).encode('utf-8') + b'\x00')
    go_back_and_write(material_file, material_name_location, '>I', material_file.tell() - 24)
    material_file.write(str(root[location_list[6]].text).encode('utf-8') + b'\x00')
    length_of_my_strings = len(str(root[location_list[5]].text).encode('utf-8') + b'\x00' +
                               str(root[location_list[5]].text).encode('utf-8') + b'\x00' +
                               str(root[location_list[6]].text).encode('utf-8') + b'\x00')
    fill_in_zeroes(material_file, length_of_my_strings)
    go_back_and_write(material_file, point_to_parameter_list, '>I', material_file.tell() - 24)
    parameter_location_list = []
    for i in range(len(parameter_list)):
        parameter_location_list.append(material_file.tell())
        pointers_locations.append(material_file.tell() - 24)
        material_file.write(struct.pack('>i', 0))
    for i in range(len(parameter_list)):
        go_back_and_write(material_file, parameter_location_list[i], '>I', material_file.tell() - 24)
        material_file.write(b'\x00\x00\x01\x00')
        name_start = material_file.tell()
        pointers_locations.append(name_start - 24)
        material_file.write(struct.pack('>I', 0))
        params_start = material_file.tell()
        pointers_locations.append(params_start - 24)
        material_file.write(struct.pack('>I', 0))
        name = str(root[location_list[7]][i].tag).encode('utf-8') + b'\x00'
        go_back_and_write(material_file, name_start, '>I', material_file.tell() - 24)
        material_file.write(name)
        fill_in_zeroes(material_file, len(name))
        go_back_and_write(material_file, params_start, '>I', material_file.tell() - 24)
        for child in root[location_list[7]][i]:
            material_file.write(struct.pack('>f', float(child.text)))
    write_footer(material_file, pointers_locations, offset_final_table, offset_final_table_abs)
    material_file.close()
    write_texset(filepath, texture_list)


def write_material_v3(root, filepath, location_list, parameter_list, texture_list):
    mat_file = open(f"{os.path.split(filepath)[0] or '.'}/{os.path.split(filepath)[1].split('.')[0]}.material", 'wb')
    pointers_locations = []
    offset_final_table, offset_final_table_abs = write_header(mat_file, 3)
    write_v3_data(mat_file, root, location_list, parameter_list, texture_list, 24, pointers_locations)
    write_footer(mat_file, pointers_locations, offset_final_table, offset_final_table_abs)
    mat_file.close()


def write_material_lw(root, filepath, location_list, parameter_list, texture_list):
    mat_file = open(f"{os.path.split(filepath)[0] or '.'}/{os.path.split(filepath)[1].split('.')[0]}.material", 'wb')
    base = 16
    pointers_locations = []
    mat_file.write(b'\x00' * base)
    root_chunk_start = mat_file.tell()
    mat_file.write(b'\x00' * 4)
    mat_file.write(struct.pack('>I', 1))
    mat_file.write(b'Material')
    ctx_chunk_start = mat_file.tell()
    mat_file.write(b'\x00' * 4)
    mat_file.write(struct.pack('>I', 3))
    mat_file.write(b'Contexts')
    write_v3_data(mat_file, root, location_list, parameter_list, texture_list, base, pointers_locations)
    pad = (16 - (mat_file.tell() % 16)) % 16
    mat_file.write(b'\x00' * pad)
    ctx_end = mat_file.tell()
    go_back_and_write(mat_file, ctx_chunk_start, '>I', ((ctx_end - ctx_chunk_start) & 0x1FFFFFFF) | (3 << 29))
    root_end = mat_file.tell()
    go_back_and_write(mat_file, root_chunk_start, '>I', ((root_end - root_chunk_start) & 0x1FFFFFFF) | (2 << 29))
    final_table_address = mat_file.tell()
    for ptr in pointers_locations:
        mat_file.write(struct.pack('>I', ptr))
    file_size = mat_file.tell()
    go_back_and_write(mat_file, 0, '>I', 0x80000000 | file_size)
    go_back_and_write(mat_file, 4, '>I', MIRAGE_SIG)
    go_back_and_write(mat_file, 8, '>I', final_table_address)
    go_back_and_write(mat_file, 12, '>I', len(pointers_locations))
    mat_file.close()


def write_material(root, filepath, location_list, parameter_list, texture_list):
    version = int(root[location_list[0]].text)
    mirage_header = root[location_list[1]].text.lower() == 'true'
    if mirage_header:
        write_material_lw(root, filepath, location_list, parameter_list, texture_list)
    elif version == 3:
        write_material_v3(root, filepath, location_list, parameter_list, texture_list)
    else:
        write_material_v1(root, filepath, location_list, parameter_list, texture_list)

def open_xml(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    ver_loc, mhdr_loc, alpha_loc, tsided_loc, add_loc, shd_loc, mat_loc, par_loc, tex_loc = 0,0,0,0,0,0,0,0,0
    par_list = []
    tex_list = []
    if root.tag == "Material":
        for i in range(len(root)):
            if root[i].tag == "version":
                ver_loc = i
            elif root[i].tag == "mirage_header":
                mhdr_loc = i
            elif root[i].tag == "Alpha_threshold":
                alpha_loc = i
            elif root[i].tag == "Two_sided":
                tsided_loc = i
            elif root[i].tag == "Additive":
                add_loc = i
            elif root[i].tag == "Shader":
                shd_loc = i
            elif root[i].tag == "Material_Name":
                mat_loc = i
            elif root[i].tag == "Parameters":
                par_loc = i
                for parameter in range(len(root[i])):
                    par_list.append([])
                    par_list[parameter].append(root[i][parameter].tag)
                    for par_param in root[i][parameter]:
                        if par_param.tag == "value_X":
                            par_list[parameter].append(par_param.text)
                    for par_param in root[i][parameter]:
                        if par_param.tag == "value_Y":
                            par_list[parameter].append(par_param.text)
                    for par_param in root[i][parameter]:
                        if par_param.tag == "value_Z":
                            par_list[parameter].append(par_param.text)
                    for par_param in root[i][parameter]:
                        if par_param.tag == "value_W":
                            par_list[parameter].append(par_param.text)
            elif root[i].tag == "Textures":
                tex_loc = i
                for texture in range(len(root[i])):
                    tex_list.append([])
                    if root[i][texture].tag != "Missing_texture":
                        #tex_list[texture].append(root[i][texture].tag)
                        for tex_param in root[i][texture]:
                            if tex_param.tag == "name":
                                tex_list[texture].append(tex_param.text)
                        for tex_param in root[i][texture]:
                            if tex_param.tag == "U_wrap":
                                tex_list[texture].append(tex_param.text)
                        for tex_param in root[i][texture]:
                            if tex_param.tag == "V_wrap":
                                tex_list[texture].append(tex_param.text)
                        for tex_param in root[i][texture]:
                            if tex_param.tag == "texture_file":
                                tex_list[texture].append(tex_param.text)
                        for tex_param in root[i][texture]:
                            if tex_param.tag == "texture_type":
                                tex_list[texture].append(tex_param.text)
        loc_list = [ver_loc,mhdr_loc,alpha_loc,tsided_loc,add_loc,shd_loc,mat_loc,par_loc,tex_loc]
        write_material(root, filepath,loc_list, par_list, tex_list)
    else:
        print("Not a 'Material' xml file")


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
    node = int(mat_file.read(4).hex(), 16)
    par_name_st = int(mat_file.read(4).hex(), 16)
    par_loc_st = int(mat_file.read(4).hex(), 16)
    par_name = read_string(par_name_st+offset, mat_file)
    mat_file.seek(par_loc_st+offset)
    Parameter = ET.SubElement(Parameters, par_name)
    ET.SubElement(Parameter, "value_X").text = str(round(iee754(mat_file.read(4).hex()), 5))
    ET.SubElement(Parameter, "value_Y").text = str(round(iee754(mat_file.read(4).hex()), 5))
    ET.SubElement(Parameter, "value_Z").text = str(round(iee754(mat_file.read(4).hex()), 5))
    ET.SubElement(Parameter, "value_W").text = str(round(iee754(mat_file.read(4).hex()), 5))

def open_texture(file_path, folder_path):
    try:
        texture = open(f'{folder_path}/{file_path}.texture','rb')
        texture_fsize = int(texture.read(4).hex(), 16)
        texture_version = int(texture.read(4).hex(), 16)
        texture_offset_final_table = int(texture.read(4).hex(), 16)
        texture_root_node_offset = int(texture.read(4).hex(), 16)
        texture_offset_final_table_abs = int(texture.read(4).hex(), 16)
        texture_padding1 = int(texture.read(4).hex(), 16)
        texture_fname_l = int(texture.read(4).hex(), 16)
        texture_padding2 = int(texture.read(1).hex(), 16)
        texture_U_wrap = int(texture.read(1).hex(), 16)
        texture_V_wrap = int(texture.read(1).hex(), 16)
        texture_padding3 = int(texture.read(1).hex(), 16)
        texture_type_l = int(texture.read(4).hex(), 16)
        return (read_string(texture_fname_l+texture_root_node_offset, texture),
                read_string(texture_type_l+texture_root_node_offset, texture),
                texture_U_wrap, texture_V_wrap)
    except FileNotFoundError:
        print(f"couldn't find texture: {folder_path}/{file_path}.texture")
        return ("Missing_texture","None",0,0)

def open_texset(file_path, xml_tree, folder_path):
    try:
        texset = open(f'{folder_path}/{file_path}.texset', 'rb')
        texset_fsize = int(texset.read(4).hex(), 16)
        texset_version = int(texset.read(4).hex(), 16)
        texset_offset_final_table = int(texset.read(4).hex(), 16)
        texset_root_node_offset = int(texset.read(4).hex(), 16)
        texset_offset_final_table_abs = int(texset.read(4).hex(), 16)
        texset_padding = int(texset.read(4).hex(), 16)
        texset_amnt_textures = int(texset.read(4).hex(), 16)
        texset_locats_start = int(texset.read(4).hex(), 16)
        Textures = ET.SubElement(xml_tree, "Textures")
        Wrap_definitions = ET.Comment("Wrap modes are: \n0-Repeat \n1-Mirror \n2-Clamp \n3-MirrorOnce \n4-Border(Extend)")
        Textures.insert(0, Wrap_definitions)
        for i in range(texset_amnt_textures):
            cur_texture_name = str(read_string(int(texset.read(4).hex(), 16) + texset_root_node_offset, texset))
            texset.seek(texset_locats_start + texset_root_node_offset + 4 * (i + 1))
            texture_file, texture_type, texture_U, texture_V = open_texture(cur_texture_name, folder_path)
            if texture_file == "Missing_texture":
                ET.SubElement(Textures, "Missing_texture")
            else:
                Texture = ET.SubElement(Textures, "texture")
                ET.SubElement(Texture, "name").text = str(cur_texture_name)
                ET.SubElement(Texture, "U_wrap").text = str(texture_U)
                ET.SubElement(Texture, "V_wrap").text = str(texture_V)
                ET.SubElement(Texture, "texture_file").text = str(texture_file)
                ET.SubElement(Texture, "texture_type").text = str(texture_type)
    except FileNotFoundError:
        print(f"couldn't found texset: '{folder_path}/{file_path}.texset")
        ET.SubElement(xml_tree, "No_texset_available")

MIRAGE_SIG = 0x0133054A
LW_ROOT_ADDR = 16

def read4be(f):
    return int(f.read(4).hex(), 16)

def find_lw_contexts(mat_file):
    def scan(f):
        start = f.tell()
        packed = read4be(f)
        value = read4be(f)
        name = f.read(8).decode('ascii', errors='replace').rstrip()
        flags = packed >> 29
        size = packed & 0x1FFFFFFF
        end = start + size
        children = []
        if not (flags & 1):
            while True:
                child = scan(f)
                children.append(child)
                if child['last']:
                    break
        data_addr = f.tell()
        f.seek(end)
        return {'name': name, 'data_addr': data_addr, 'last': bool(flags & 2), 'children': children}
    mat_file.seek(LW_ROOT_ADDR)
    root_node = scan(mat_file)
    for child in root_node['children']:
        if child['name'].rstrip() == 'Contexts':
            return child['data_addr']
    return None

def read_v3_gens(mat_file, root_elem, base, mat_name):
    shader_loc = read4be(mat_file)
    sub_shader_loc = read4be(mat_file)
    texset_loc = read4be(mat_file)
    texture_loc = read4be(mat_file)
    alpha_threshold = int(mat_file.read(1).hex(), 16)
    two_sided = int(mat_file.read(1).hex(), 16)
    additive = int(mat_file.read(1).hex(), 16)
    mat_file.read(1)
    ET.SubElement(root_elem, "Alpha_threshold").text = str(alpha_threshold)
    ET.SubElement(root_elem, "Two_sided").text = str(two_sided)
    ET.SubElement(root_elem, "Additive").text = str(additive)
    param_count = int(mat_file.read(1).hex(), 16)
    mat_file.read(1)
    mat_file.read(1)
    texture_count = int(mat_file.read(1).hex(), 16)
    params_start = read4be(mat_file)
    read4be(mat_file)
    read4be(mat_file)
    ET.SubElement(root_elem, "Shader").text = read_string(shader_loc + base, mat_file)
    ET.SubElement(root_elem, "Material_Name").text = mat_name
    mat_file.seek(params_start + base)
    pos = mat_file.tell()
    Parameters = ET.SubElement(root_elem, "Parameters")
    for i in range(param_count):
        read_param(read4be(mat_file), Parameters, mat_file, base)
        mat_file.seek(pos + 4 * (i + 1))
    if texture_count > 0:
        Textures = ET.SubElement(root_elem, "Textures")
        Textures.insert(0, ET.Comment("Wrap modes are: \n0-Repeat \n1-Mirror \n2-Clamp \n3-MirrorOnce \n4-Border(Extend)"))
        unit_names = []
        mat_file.seek(texset_loc + base)
        for i in range(texture_count):
            unit_ptr = read4be(mat_file)
            save = mat_file.tell()
            unit_names.append(read_string(unit_ptr + base, mat_file))
            mat_file.seek(save)
        mat_file.seek(texture_loc + base)
        for i in range(texture_count):
            tex_ptr = read4be(mat_file)
            save = mat_file.tell()
            mat_file.seek(tex_ptr + base)
            fname_ptr = read4be(mat_file)
            flags = read4be(mat_file)
            type_ptr = read4be(mat_file)
            Tex = ET.SubElement(Textures, "texture")
            ET.SubElement(Tex, "name").text = unit_names[i]
            ET.SubElement(Tex, "U_wrap").text = str((flags >> 16) & 0xFF)
            ET.SubElement(Tex, "V_wrap").text = str((flags >> 8) & 0xFF)
            ET.SubElement(Tex, "texture_file").text = read_string(fname_ptr + base, mat_file)
            ET.SubElement(Tex, "texture_type").text = read_string(type_ptr + base, mat_file)
            mat_file.seek(save)


def convert_mat_to_xml(input_file):
    mat_file = open(input_file, 'rb')
    folder = os.path.split(input_file)[0] or '.'
    mat_name = os.path.splitext(os.path.basename(input_file))[0]
    root = ET.Element("Material")
    fsize = read4be(mat_file)
    raw_version = read4be(mat_file)
    mirage_header = raw_version == MIRAGE_SIG
    version = 3 if mirage_header else raw_version
    ET.SubElement(root, "version").text = str(version)
    ET.SubElement(root, "mirage_header").text = str(mirage_header).lower()
    if mirage_header:
        ctx_addr = find_lw_contexts(mat_file)
        if ctx_addr is None:
            print("Could not find Contexts node in LW material")
            return
        mat_file.seek(ctx_addr)
        read_v3_gens(mat_file, root, LW_ROOT_ADDR, mat_name)
    elif version == 3:
        read4be(mat_file)
        root_node_offset = read4be(mat_file)
        read4be(mat_file)
        read4be(mat_file)
        read_v3_gens(mat_file, root, root_node_offset, mat_name)
    else:
        read4be(mat_file)
        root_node_offset = read4be(mat_file)
        read4be(mat_file)
        read4be(mat_file)
        shader_location1 = read4be(mat_file)
        shader_location2 = read4be(mat_file)
        mat_name_loc = read4be(mat_file)
        read4be(mat_file)
        alpha_threshold = int(mat_file.read(1).hex(), 16)
        two_sided = int(mat_file.read(1).hex(), 16)
        additive = int(mat_file.read(1).hex(), 16)
        mat_file.read(1)
        ET.SubElement(root, "Alpha_threshold").text = str(alpha_threshold)
        ET.SubElement(root, "Two_sided").text = str(two_sided)
        ET.SubElement(root, "Additive").text = str(additive)
        amount_of_params = int(mat_file.read(1).hex(), 16)
        mat_file.read(3)
        parameters_start = read4be(mat_file)
        read4be(mat_file)
        read4be(mat_file)
        ET.SubElement(root, "Shader").text = read_string(shader_location1 + root_node_offset, mat_file)
        v1_mat_name = read_string(mat_name_loc + root_node_offset, mat_file)
        ET.SubElement(root, "Material_Name").text = v1_mat_name
        mat_file.seek(parameters_start + root_node_offset)
        pos = mat_file.tell()
        Parameters = ET.SubElement(root, "Parameters")
        for i in range(amount_of_params):
            read_param(read4be(mat_file), Parameters, mat_file, root_node_offset)
            mat_file.seek(pos + 4 * (i + 1))
        open_texset(v1_mat_name, root, folder)
    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(f"{folder}/{mat_name}.xml")


if len(sys.argv) < 2:
    print("Usage: python to_material.py <input.material|input.xml>")
    sys.exit(1)

input_path = sys.argv[1]
ext = os.path.splitext(input_path)[1].lower()

if ext == ".material":
    convert_mat_to_xml(input_path)
elif ext == ".xml":
    open_xml(input_path)
else:
    print("Unsupported file type. Provide a .material or .xml file.")
    sys.exit(1)
