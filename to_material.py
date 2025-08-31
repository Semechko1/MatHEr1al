import os.path
import struct
import xml.etree.ElementTree as ET

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
        texture_file = open(f"{os.path.split(filepath)[0]}/{texture_list[indexes_list[i]][0]}.texture", 'wb')
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
    texset_file = open(f"{os.path.split(filepath)[0]}/{os.path.split(filepath)[1].split('.')[0]}.texset", 'wb')
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


def write_material(root, filepath, location_list, parameter_list, texture_list):
    #tree = ET.parse(filepath)
    #root = tree.getroot()
    material_file = open(f"{os.path.split(filepath)[0]}/{os.path.split(filepath)[1].split('.')[0]}.material", 'wb')
    pointers_locations = []

    offset_final_table, offset_final_table_abs = write_header(material_file, int(root[location_list[0]].text))
    #end of header

    shader_location1 = material_file.tell()
    pointers_locations.append(shader_location1-24)
    material_file.write(struct.pack('>I', 0)) # pointer to Shdr1
    shader_location2 = material_file.tell()
    pointers_locations.append(shader_location2-24)
    material_file.write(struct.pack('>I', 0)) # pointer to Shdr2
    material_name_location = material_file.tell()
    pointers_locations.append(material_name_location-24)
    material_file.write(struct.pack('>I', 0)) # pointer to mat_name
    pointers_locations.append(material_file.tell()-24)
    material_file.write(struct.pack('>i', 0)) # padding?

    material_file.write(struct.pack('>B',int(root[location_list[1]].text))) #alpha_threshold
    material_file.write(struct.pack('>B',int(root[location_list[2]].text))) #2-sided
    material_file.write(struct.pack('>B',int(root[location_list[3]].text))) #additive
    material_file.write(struct.pack('>B',0)) #padding?

    #amount_of_params = material_file.tell()
    #pointers_locations.append()
    material_file.write(struct.pack('<I',int(len(parameter_list)))) #amount of parameters

    point_to_parameter_list = material_file.tell()
    pointers_locations.append(point_to_parameter_list-24)
    material_file.write(struct.pack('>I',0)) #pointer to where pointers to parameters are listed
    material_file.write(struct.pack('>i', 0))  # padding?
    material_file.write(struct.pack('>i', 0))  # padding?

    go_back_and_write(material_file, shader_location1, ">I",material_file.tell()-24)
    material_file.write(str(root[location_list[4]].text).encode('utf-8') + b'\x00')
    go_back_and_write(material_file, shader_location2, ">I", material_file.tell()-24)
    material_file.write(str(root[location_list[4]].text).encode('utf-8') + b'\x00')
    go_back_and_write(material_file, material_name_location, ">I", material_file.tell()-24)
    material_file.write(str(root[location_list[5]].text).encode('utf-8') + b'\x00')
    length_of_my_strings = len(str(root[location_list[4]].text).encode('utf-8') + b'\x00' +
                               str(root[location_list[4]].text).encode('utf-8') + b'\x00' +
                               str(root[location_list[5]].text).encode('utf-8') + b'\x00')
    fill_in_zeroes(material_file, length_of_my_strings)


    go_back_and_write(material_file,point_to_parameter_list,">I",material_file.tell()-24)
    parameter_location_list = []
    for i in range(len(parameter_list)):
        parameter_location_list.append(material_file.tell())
        pointers_locations.append(material_file.tell()-24)
        material_file.write(struct.pack('>i',0))
    for i in range(len(parameter_list)):
        go_back_and_write(material_file,parameter_location_list[i],'>I',material_file.tell()-24)
        material_file.write(b'\x00\00\01\00') #node
        name_start = material_file.tell()
        pointers_locations.append(name_start-24)
        material_file.write(struct.pack('>I',0))
        params_start = material_file.tell()
        pointers_locations.append(params_start-24)
        material_file.write(struct.pack('>I',0))
        name = str(root[location_list[6]][i].tag).encode('utf-8') + b'\x00'
        go_back_and_write(material_file,name_start,'>I',material_file.tell()-24)
        material_file.write(name)
        fill_in_zeroes(material_file, len(name))
        go_back_and_write(material_file,params_start,'>I',material_file.tell()-24)
        for child in root[location_list[6]][i]:
            val = float(child.text)
            #print(root[location_list[6]][i].tag, child.tag, child.text)
            material_file.write(struct.pack('>f',val))

    #offset_table
    write_footer(material_file, pointers_locations, offset_final_table, offset_final_table_abs)
    material_file.close()
    write_texset(filepath, texture_list)

def open_xml(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    ver_loc, alpha_loc, tsided_loc, add_loc, shd_loc, mat_loc, par_loc, tex_loc = 0,0,0,0,0,0,0,0
    par_list = []
    tex_list = []
    if root.tag == "Material":
        for i in range(len(root)):
            if root[i].tag == "version":
                ver_loc = i
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
        loc_list = [ver_loc,alpha_loc,tsided_loc,add_loc,shd_loc,mat_loc,par_loc,tex_loc]
        #print(loc_list)
        #print(par_list)
        #print(tex_list)
        write_material(root, filepath,loc_list, par_list, tex_list)
    else:
        print("Not a 'Material' xml file")


open_xml("te.st/chains.xml")
