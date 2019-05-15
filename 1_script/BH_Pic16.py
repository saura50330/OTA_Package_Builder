import sys
import time
import serial
import os

'''
#define WR_FLH 1
#define WR_EEP (WR_FLH+1)
#define RD_FLH 3
#define RD_EEP (RD_FLH +1)
#define PING 5
#define RSTCMD 6
#define POS_RES 10

'''
START_ADD=0x200
Hex_File_Path=""
# "C:\Python27\python.exe C:\Users\acer\Desktop\MASTER_DOCUMENT_V1\START_UP\microchip\boot_loder\bt_ldr\2_Bootloader_Design\boot_loader_Script\BH_Pic16.py"
resp_info=[]
ext_add =0
image_checksum = 0
byt_cnt = 0
def split_array(arr, size):
     arrs = []
     while len(arr) > size:
         pice = arr[:size]
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arrs
def split_by_n( seq, n ):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:n]
        seq = seq[n:]
def Flash_verify():
	list_read=[0x03,0x00,0x02]
	address = 0x200
	while(address<=0x300):
		send_data(list_read)
		address=address+1
		list_read[1]=address&0xFF
		list_read[2]=(address>>8)&0xFF
		time.sleep(BREAK)
		tmp_info = ser.read(3)
		if len(tmp_info) == 0:
			print("READ TIMEOUT")
		else:
			#print int(tmp_info[1:3].encode("hex"), 16), " ",
			print (tmp_info[1].encode("hex") + " " + tmp_info[2].encode("hex")), # note , after print will not add new line
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		
def Write_Hex_64(file_path):
	global temp
	bl_frame_64_data = ""
	bl_frame_64_add =0
	eep_frame=[]
	ext_add=0
	image_checksum = 0 # flash mem checksum
	byt_cnt = 0  
	frame_cnt=1
	# 1 command , 2 address ,64 data bytes
	bl_frame_64_new_add_prv=0
	length_prv=0
	try:
		f = open(file_path,'r')
		for line in f:
			length = int(line[1:3],16)/2 			# data length in bytes# 1st two chrecter are length  # 1:3 mease extrect 1 and 2nd charecter from line #int(line[1:2], 16)
			address = int(line[3:7],16) | (ext_add<<16) 	# hex file address	# 3rd 4th 5th and 6th char are address 
			dat_type =  int(line[7:9],16)
			line_lnt=len(line)
			if (line_lnt > 3):
				data=line[9:(line_lnt-3)]  # data field
			else:
				data=""
				print("\n invalid line lnth")
				break
			checksum = int(line[(line_lnt-3):(line_lnt-1)],16) #checksum of line
			bl_frame_64_new_add=(address/2)
			if(length == 0): # end of hex file
				#print(eep_frame)
				break
			elif(dat_type == 4) : # if it extended addrss update the same
					ext_add = int(data,16)
					#bl_frame_64_data = bl_frame_64_data + "00"*((32-((bl_frame_64_new_add_prv +length_prv)%32))*2)
			elif(ext_add!=0): # its eeprom data or config data
				if(bl_frame_64_new_add>=0xF000):# its eeprom data 
					temp_data=list(split_by_n(data,4)) # eeprom data have some extra byte to be ignored in hex file
					temp_add=bl_frame_64_new_add
					for index in range(len(temp_data)):
						eep_frame.append(0x02)
						eep_frame.append(temp_add&0xFF)
						eep_frame.append((temp_add>>8)&0xFF)
						eep_frame.append(((int(temp_data[index], 16))>>8)&0xFF)
						temp_add  = temp_add +1
			else: # its program data			
				if(bl_frame_64_new_add_prv !=0):
					if((bl_frame_64_new_add_prv + length_prv) != bl_frame_64_new_add):
						bl_frame_64_data = bl_frame_64_data + "00"*((bl_frame_64_new_add - (bl_frame_64_new_add_prv + length_prv))*2)
					bl_frame_64_data = bl_frame_64_data + str(data)
				else:
					bl_frame_64_data = bl_frame_64_data + str(data) # add new ata
			length_prv=length
			bl_frame_64_new_add_prv=bl_frame_64_new_add
	finally:
		  f.close()
	list_b=list(split_by_n(bl_frame_64_data,128)) # split each byte
	temp_add = START_ADD
	bl_data_64_farme = []
	New_Hex_File_Path=Hex_File_Path.replace('.','_New.')
	thefile = open(New_Hex_File_Path, 'w')
	print("Programing Flash Memory")
	for index in range(len(list_b)):
		list_Temp = list_b[index]
		list_Temp = list(split_by_n(list_Temp,2))
		#print(list_Temp)
		
		bl_data_64_farme.append(0x01)
		bl_data_64_farme.append(temp_add & 0xFF)
		bl_data_64_farme.append((temp_add >> 8)&0xFF)
		for index in range(len(list_Temp)):
			image_checksum = image_checksum + ((int(list_Temp[index], 16)) & 0xFF) # flash mem checksum
			bl_data_64_farme.append(int(list_Temp[index], 16))
			byt_cnt = byt_cnt + 1
		#print(bl_data_64_farme)
		#print("\n")
		send_data(bl_data_64_farme)
		temp_data=str(bl_data_64_farme)
		temp_data=temp_data.replace("[", "")
		temp_data=temp_data.replace(",", "")
		temp_data=temp_data.replace("]", "")
		thefile.write(temp_data + "\n")
		time.sleep(BREAK*2)
		temp&=reponce("WRITE CMD ",0x01)
		temp_add = temp_add + 0x20;
		del bl_data_64_farme[:]
	time.sleep(BREAK)
	if(temp == 0):
		print("\nLog: At least one Flesh WRITE CMD Failed")
	eep_frame=list(split_array(eep_frame,4)) # 16 cherecters in eep write command
	if(len(eep_frame)>1):
		print("Programming EEPROM")
		#print len(eep_frame)
		for index in range(len(eep_frame)):
			#print (eep_frame[index]),
			send_data(eep_frame[index])
			temp_data=str(eep_frame[index])
			temp_data=temp_data.replace("[", "")
			temp_data=temp_data.replace(",", "")
			temp_data=temp_data.replace("]", "")
			thefile.write(temp_data + "\n")
			time.sleep(BREAK)
	image_checksum = image_checksum & 0xFF
	send_data([2, 241, 240, image_checksum])
	print "Image checksum : " + image_checksum + "data lnt: " +  byt_cnt 
	thefile.write("2 241 240 " + str(image_checksum) + "170\n") # write image_checksum
	thefile.close()	
def Write_Hex_to_String_64(file_path):
	global temp
	bl_frame_64_data = ""
	bl_frame_64_add =0
	eep_frame=[]
	ext_add=0
	image_checksum = 0
	byt_cnt =0
	frame_cnt=1
	# 1 command , 2 address ,64 data bytes
	bl_frame_64_new_add_prv=0
	length_prv=0
	try:
		f = open(file_path,'r')
		for line in f:
			length = int(line[1:3],16)/2 			# data length in bytes# 1st two chrecter are length  # 1:3 mease extrect 1 and 2nd charecter from line #int(line[1:2], 16)
			address = int(line[3:7],16) | (ext_add<<16) 	# hex file address	# 3rd 4th 5th and 6th char are address 
			dat_type =  int(line[7:9],16)
			line_lnt=len(line)
			if (line_lnt > 3):
				data=line[9:(line_lnt-3)]  # data field
			else:
				data=""
				print("\n invalid line lnth")
				break
			checksum = int(line[(line_lnt-3):(line_lnt-1)],16) #checksum of line
			bl_frame_64_new_add=(address/2)
			if(length == 0): # end of hex file
				#print(eep_frame)
				break
			elif(dat_type == 4) : # if it extended addrss update the same
					ext_add = int(data,16)
					#bl_frame_64_data = bl_frame_64_data + "00"*((32-((bl_frame_64_new_add_prv +length_prv)%32))*2)
			elif(ext_add!=0): # its eeprom data or config data
				if(bl_frame_64_new_add>=0xF000):# its eeprom data 
					temp_data=list(split_by_n(data,4)) # eeprom data have some extra byte to be ignored in hex file
					temp_add=bl_frame_64_new_add
					for index in range(len(temp_data)):
						eep_frame.append(0x02)
						eep_frame.append(temp_add&0xFF)
						eep_frame.append((temp_add>>8)&0xFF)
						eep_frame.append(((int(temp_data[index], 16))>>8)&0xFF)
						temp_add  = temp_add +1
			else: # its program data			
				if(bl_frame_64_new_add_prv !=0):
					if((bl_frame_64_new_add_prv + length_prv) != bl_frame_64_new_add):
						bl_frame_64_data = bl_frame_64_data + "00"*((bl_frame_64_new_add - (bl_frame_64_new_add_prv + length_prv))*2)
					bl_frame_64_data = bl_frame_64_data + str(data)
				else:
					bl_frame_64_data = bl_frame_64_data + str(data) # add new ata
			length_prv=length
			bl_frame_64_new_add_prv=bl_frame_64_new_add
	finally:
		  f.close()
	list_b=list(split_by_n(bl_frame_64_data,128)) # split each byte
	temp_add = START_ADD
	bl_data_64_farme = []
	New_Hex_File_Path=os.path.splitext(Hex_File_Path)[0]
	New_Hex_File_Path=New_Hex_File_Path + ".OTA"
	thefile = open(New_Hex_File_Path, 'w')
	thefile.write("7\n") # insert reflash command
	thefile.write("255 0 0 0\n") # insert dummy command for delay to recover
	thefile.write("255 0 0 0\n") # insert dummy command for delay to recover
	thefile.write("255 0 0 0\n") # insert dummy command for delay to recover
	thefile.write("255 0 0 0\n") # insert dummy command for delay to recover
	thefile.write("2 240 240 255\n") # make application Invalid
	thefile.write("2 242 240 255\n") # make application version 255 
	for index in range(len(list_b)):
		list_Temp = list_b[index]
		list_Temp = list(split_by_n(list_Temp,2))
		#print(list_Temp)
		bl_data_64_farme.append(0x01)
		bl_data_64_farme.append(temp_add & 0xFF)
		bl_data_64_farme.append((temp_add >> 8)&0xFF)
		for index in range(len(list_Temp)):
			image_checksum = image_checksum + ((int(list_Temp[index], 16)) & 0xFF) # flash mem checksum
			byt_cnt = byt_cnt + 1
			bl_data_64_farme.append(int(list_Temp[index], 16))
		#print(bl_data_64_farme)
		#print("\n")
		temp_data=str(bl_data_64_farme)
		temp_data=temp_data.replace("[", "")
		temp_data=temp_data.replace(",", "")
		temp_data=temp_data.replace("]", "")
		thefile.write(temp_data + "\n")
		temp_add = temp_add + 0x20;
		del bl_data_64_farme[:]
	eep_frame=list(split_array(eep_frame,4)) # 16 cherecters in eep write command
	if(len(eep_frame)>1):
		print("writing  EEPROM data")
		#print len(eep_frame)
		for index in range(len(eep_frame)):
			#print (eep_frame[index]),
			temp_data=str(eep_frame[index])
			temp_data=temp_data.replace("[", "")
			temp_data=temp_data.replace(",", "")
			temp_data=temp_data.replace("]", "")
			thefile.write(temp_data + "\n")
	image_checksum = image_checksum & 0xFF
	print "Image checksum : " + str(image_checksum) + "data lnt: " + str(byt_cnt)
	thefile.write("2 241 240 " + str(image_checksum) + "\n") # write image_checksum
	thefile.write("2 240 240 170\n") # make application valid
	thefile.close()	
	
def Write_Hex_to_bin_64(file_path):
	global temp
	bl_frame_64_data = ""
	bl_frame_64_add =0
	eep_frame=[]
	ext_add=0
	checksum = 0
	frame_cnt=1
	# 1 command , 2 address ,64 data bytes
	bl_frame_64_new_add_prv=0
	length_prv=0
	try:
		f = open(file_path,'r')
		for line in f:
			length = int(line[1:3],16)/2 			# data length in bytes# 1st two chrecter are length  # 1:3 mease extrect 1 and 2nd charecter from line #int(line[1:2], 16)
			address = int(line[3:7],16) | (ext_add<<16) 	# hex file address	# 3rd 4th 5th and 6th char are address 
			dat_type =  int(line[7:9],16)
			line_lnt=len(line)
			if (line_lnt > 3):
				data=line[9:(line_lnt-3)]  # data field
			else:
				data=""
				print("\n invalid line lnth")
				break
			checksum = int(line[(line_lnt-3):(line_lnt-1)],16) #checksum of line
			bl_frame_64_new_add=(address/2)
			if(length == 0): # end of hex file
				#print(eep_frame)
				break
			elif(dat_type == 4) : # if it extended addrss update the same
					ext_add = int(data,16)
					bl_frame_64_data = bl_frame_64_data + "00"*((32-((bl_frame_64_new_add_prv +length_prv)%32))*2)
			elif(ext_add!=0): # its eeprom data or config data
				if(bl_frame_64_new_add>=0xF000):# its eeprom data 
					temp_data=list(split_by_n(data,4)) # eeprom data have some extra byte to be ignored in hex file
					temp_add=bl_frame_64_new_add
					for index in range(len(temp_data)):
						eep_frame.append(0x02)
						eep_frame.append(temp_add&0xFF)
						eep_frame.append((temp_add>>8)&0xFF)
						eep_frame.append(((int(temp_data[index], 16))>>8)&0xFF)
						temp_add  = temp_add +1
			else: # its program data			
				if(bl_frame_64_new_add_prv !=0):
					if((bl_frame_64_new_add_prv + length_prv) != bl_frame_64_new_add):
						bl_frame_64_data = bl_frame_64_data + "00"*((bl_frame_64_new_add - (bl_frame_64_new_add_prv + length_prv))*2)
					bl_frame_64_data = bl_frame_64_data + str(data)
				else:
					bl_frame_64_data = bl_frame_64_data + str(data) # add new ata
			length_prv=length
			bl_frame_64_new_add_prv=bl_frame_64_new_add
	finally:
		  f.close()
	list_b=list(split_by_n(bl_frame_64_data,128)) # split each byte
	temp_add = START_ADD
	bl_data_64_farme = []
	New_Hex_File_Path=Hex_File_Path.replace('.','_Bin.')
	thefile = open(New_Hex_File_Path, 'w')
	print("Creating OTA file...\n")
	for index in range(len(list_b)):
		list_Temp = list_b[index]
		list_Temp = list(split_by_n(list_Temp,2))
		#print(list_Temp)
		
		bl_data_64_farme.append(0x01)
		bl_data_64_farme.append(temp_add & 0xFF)
		bl_data_64_farme.append((temp_add >> 8)&0xFF)
		for index in range(len(list_Temp)):
			checksum = checksum + int(list_Temp[index], 16) # flash mem checksum
			bl_data_64_farme.append(int(list_Temp[index], 16))
		#print(bl_data_64_farme)
		#print("\n")
		newFileByteArray = bytearray(bl_data_64_farme)		
		thefile.write(newFileByteArray)
		temp_add = temp_add + 0x20;
		del bl_data_64_farme[:]
	time.sleep(BREAK)
	eep_frame=list(split_array(eep_frame,4)) # 16 cherecters in eep write command
	if(len(eep_frame)>1):
		print("writing EEP data to OTA file")
		#print len(eep_frame)
		for index in range(len(eep_frame)):
			#print (eep_frame[index])
			newFileByteArray = bytearray(eep_frame[index])		
			thefile.write(newFileByteArray)
	thefile.close()	
	
def reponce(cmd,resp):
	tmp_info = ser.read(3)
	#print tmp_info
	ser.reset_input_buffer()
	ser.reset_output_buffer()
	status=0
	del resp_info[:]
	if (len(tmp_info) != 0):
		for c in tmp_info:
			resp_info.append(ord(c))
		#print resp_info
		if(resp_info[0] == resp):
			print("\nlog:" + cmd + " success" )
			status=1
		else:
			print("\nlog: " + cmd + " fail wrong resp: " + str(resp_info[0]))
	else:
		print("\nlog: " + cmd + "fail no data")
	tmp_info=0
	return status
def print_heading():
	print("\n -----------Boothost For PIC16F18313--------------\n")
	print("By Nandkumar G Dhavalikar (nandhavalikar@gmail.com)\n")
	print("K : Convert Hex to OTA\nR : Read Flash\nP : Program \nC : Clear Screen\nI : Ping\nV : Read Boot loader Version\nT : Catch BL\nH : Help \nQ : Exit \n")
def send_data(list_dat):
	ser.reset_input_buffer()
	ser.reset_output_buffer()
	for value in list_dat:
		ser.write(chr(value))
		time.sleep(0.001) # delay per charecter	

list_app_invalid = [0x02, 0xF0, 0xF0, 0x00] # [cmd add1 add0 data] write 00 at location 0x70FF of eeprom 
list_app_valid =   [0x02, 0xF0, 0xF0, 0xAA] # [cmd add1 add0 data] write 0xAA at location 0x70FF of eeprom 
list_reset = 	   [0x06]
list_ping = 	   [0x05]
list_Bl_ver = 	   [0x04, 0xFE, 0xF0] # read bl version no
BREAK=0.1 # time gap between two command
POS_RES = 10

try:
  ser = serial.Serial('COM12', 57600, timeout=0.01)
  ser.close()
except:
  print("\n\n\nERROR: NO COM PORT COM12!!! baud 57600 ")



while (1) :
	print_heading()
	option = raw_input("\nOption:") #read user input
	if ((option == 'K') or (option == 'k')):
		Hex_File_Path = raw_input("\nEnter complete Hex File path : ") #read hex file path	
		print("\n Hex File Entered : " + Hex_File_Path)
		#Write_Hex_to_bin_64(Hex_File_Path)
		Write_Hex_to_String_64(Hex_File_Path)
		
	elif ((option == 'P') or (option == 'p')):
		ser.open()
		time.sleep(1)
		temp = 0
		retry = 10
		while ((temp!=1) and (retry>0)):
			send_data(list_reset)
			time.sleep(BREAK)
			temp=reponce("RESET CMD ",0x06)
			retry = retry - 1;
		if(retry==0):
			print("\n No Response")
			ser.close()
			continue
		send_data(list_app_invalid)
		time.sleep(BREAK)
		temp=reponce("APP INVALID CMD ",0x02)
		
		Hex_File_Path = raw_input("\nEnter complete Hex File path : ") #read hex file path	
		print("\n Hex File Entered : " + Hex_File_Path)
		Write_Hex_64(Hex_File_Path)
		
		#Flash_verify();
		
		send_data(list_app_valid)
		time.sleep(BREAK)
		temp=reponce("APP VALID CMD ",0x02)
		
		send_data(list_reset)
		time.sleep(BREAK)
		temp=reponce("Programming ",0x06)
		
		ser.close()
		print("\nAPP Loader File location: " + Hex_File_Path + "_New.Hex")
	elif((option == 'C') or (option == 'c')):
		os.system('cls')
	elif((option == 'Q') or (option == 'q')):
		break
	elif((option == 'I') or (option == 'i')):
		ser.open()
		time.sleep(1)
		temp = 0
		retry = 2
		while ((temp!=1) and (retry>0)):
			send_data(list_ping)
			time.sleep(BREAK)
			temp=reponce("PING CMD ",0x05)
			retry = retry - 1;
		if(temp==0):
			print("\nNo Response")
		else:
			print("\nPING Success")
		ser.close()
	elif((option == 'V') or (option == 'v')):
		ser.open()
		time.sleep(1)
		send_data(list_Bl_ver)
		time.sleep(BREAK)
		temp=reponce("BL VER CMD ",0x04)
		if(temp):
			print("\nBL Version :" + str(resp_info[1]))
		ser.close()
	elif((option == 'T') or (option == 't')):
		ser.open()
		time.sleep(1)
		temp = 0
		retry = 10
		while ((temp!=1) and (retry>0)):
			send_data(list_reset)
			time.sleep(BREAK)
			temp=reponce("RESET CMD ",0x06)
			retry = retry - 1;
		if(retry==0):
			print("\n No Response")
			ser.close()
			continue
		send_data(list_app_invalid)
		time.sleep(BREAK)
		temp=reponce("APP INVALID CMD ",0x02)
		if(temp==0):
			print("\n Power Cycle the controller while bootloader catch retry")
		ser.close()
	elif((option == 'H') or (option == 'h')):
		print("\nGenerated APP Loader hex File location is in hex file folder with name XXX.OTA")
		print("\nUART BAUD: 57600 , COM12 ")
	else:
		print("\n Unsupported or Unimplemented")