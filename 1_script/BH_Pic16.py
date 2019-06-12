#C:\Python27\python.exe
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
'''
# ROM ADDRESSSES
FLASH_SECTOR_SIZE = 0x20  # minimum size which can be eraced 32 bytes

APP_START_ADD = 0x2A0
APP_END_ADD	  = 0x800

#EEPROM ADDRESSES
EEP_START_ADD = 0xF000
DEF_EEP_DATA = 0xFF
#--------Fectory 0xF0 is added by default ----------
EEP_FECT_DATA_VALID = 255
EEP_FECT_BL_VER = 254
EEP_FECT_DEV_TYP = 252	 
EEP_FECT_LID_3 = 251
EEP_FECT_LID_2 = 250
EEP_FECT_LID_1 = 249
EEP_FECT_LID_0 = 248

#-----------FDR------------
EEP_FDR_APP_MAC03 = 247
EEP_FDR_APP_MAC02 = 246
EEP_FDR_APP_MAC01 = 245
EEP_FDR_APP_MAC00 = 244
EEP_FDR_APP_MACOK = 243
EEP_FDR_APP_VERSN = 242
EEP_FDR_APP_CHKSM = 241
EEP_FDR_APP_VALID = 240

#-----------Command-------
FLSH_WR_CMD = 0x01
EEP_WR_CMD	= 0x02
FLSH_RD_CMD = 0x03
EEP_RD_CMD	= 0x04
PING_CMD	= 0x05
RESET_CMD	= 0x06
FLASH_CMD	= 0x07
DUMMY_DEF_CMD = 0xFF
#--------
RESPONCE_BYTE_LEN = 5
BREAK = 0.1 # time gap between two TX command

#-------DEvice type values-------
NO_DEVICE = 0xFF
DEMO = 0x01
WALL_SWITCH = 0x02

Hex_File_Path=""
# "C:\Python27\python.exe C:\Users\acer\Desktop\MASTER_DOCUMENT_V1\START_UP\microchip\boot_loder\bt_ldr\2_Bootloader_Design\boot_loader_Script\BH_Pic16.py"
resp_info=[]
ext_add = 0
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
	address = APP_START_ADD
	list_read=[FLSH_RD_CMD,(address&0xFF),((address>>8)&0xFF)]
	
	while(address < APP_END_ADD):
		send_data(list_read)
		address = address + 1
		list_read[1]=address&0xFF
		list_read[2]=(address>>8)&0xFF
		time.sleep(BREAK)
		tmp_info = ser.read(RESPONCE_BYTE_LEN)
		if len(tmp_info) == 0:
			print("READ TIMEOUT")
		else:
			#print int(tmp_info[1:3].encode("hex"), 16), " ",
			print (tmp_info[3].encode("hex") + " " + tmp_info[4].encode("hex")), # note , after print will not add new line
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		
def Write_Fect_OTA_file(file_path,Device_Type_temp):
	
	#FDR
	#SEND DEF MAC
	New_Hex_File_Path=os.path.splitext(file_path)[0]
	New_Hex_File_Path=New_Hex_File_Path + "DID_01010101.FECT" #TODO:  update this with DID serial no
	thefile = open(New_Hex_File_Path, 'w')
	
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FECT_DEV_TYP) +" 240 " + str(Device_Type_temp) + "\n") # write device type
	
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FECT_LID_0) +" 240 1\n") # write DEVICE ID	 TODO: this id t be maintaind to provide uniqu id every time it is called
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FECT_LID_1) +" 240 1\n") # write DEVICE ID
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FECT_LID_2) +" 240 1\n") # write DEVICE ID
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FECT_LID_3) +" 240 1\n") # write DEVICE ID

	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FECT_DATA_VALID) +" 240 1\n") # Fectory update completed
	
	
	# verify data
	
	thefile.close()	
def Write_Hex_to_String_64(file_path,Device_Type_temp):
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
			length = int(line[1:3],16)/2			# data length in bytes# 1st two chrecter are length	 # 1:3 mease extrect 1 and 2nd charecter from line #int(line[1:2], 16)
			address = int(line[3:7],16) | (ext_add<<16)		# hex file address	# 3rd 4th 5th and 6th char are address 
			dat_type =	int(line[7:9],16)
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
				if(bl_frame_64_new_add>=EEP_START_ADD):# its eeprom data  
					temp_data=list(split_by_n(data,4)) # eeprom data have some extra byte to be ignored in hex file
					temp_add=bl_frame_64_new_add
					for index in range(len(temp_data)):
						eep_frame.append(EEP_WR_CMD)
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
	temp_add = APP_START_ADD
	bl_data_64_farme = []
	New_Hex_File_Path=os.path.splitext(file_path)[0]
	New_Hex_File_Path=New_Hex_File_Path + ".OTA"
	thefile = open(New_Hex_File_Path, 'w')
	thefile.write(str(FLASH_CMD) + "\n") # insert reflash command
	thefile.write(str(DUMMY_DEF_CMD) + " 0 0 0\n") # insert dummy command for delay to recover
	thefile.write(str(DUMMY_DEF_CMD) + " 0 0 0\n") # insert dummy command for delay to recover
	thefile.write(str(DUMMY_DEF_CMD) + " 0 0 0\n") # insert dummy command for delay to recover
	thefile.write(str(DUMMY_DEF_CMD) + " 0 0 0\n") # insert dummy command for delay to recover
	thefile.write( str(EEP_WR_CMD) + " "+ str(EEP_FDR_APP_VALID) +" 240 " + str(DEF_EEP_DATA) + "\n") # make application Invalid basically erases device type stored in FDR 
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FDR_APP_VERSN) +" 240 "+str(DEF_EEP_DATA) + "\n") # make application version 255 
	for index in range(len(list_b)):
		list_Temp = list_b[index]
		list_Temp = list(split_by_n(list_Temp,2))
		#print(list_Temp)
		bl_data_64_farme.append(FLSH_WR_CMD)
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
		temp_add = temp_add + FLASH_SECTOR_SIZE # FLASH_SECTOR_SIZE 0x20
		del bl_data_64_farme[:]
	eep_frame=list(split_array(eep_frame,4)) # 16 cherecters in eep write command
	if(len(eep_frame)>1):
		print("writing	EEPROM data")
		#print len(eep_frame)
		for index in range(len(eep_frame)):
			#print (eep_frame[index]),
			temp_data=str(eep_frame[index])
			temp_data=temp_data.replace("[", "")
			temp_data=temp_data.replace(",", "")
			temp_data=temp_data.replace("]", "")
			thefile.write(temp_data + "\n")
	image_checksum = image_checksum & 0xFF
	print "Image checksum : " + str(image_checksum) + ", data lnt: " + str(byt_cnt)
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FDR_APP_CHKSM) + " 240 " + str(image_checksum) + "\n") # write image_checksum
	thefile.write(str(EEP_WR_CMD) + " "+ str(EEP_FDR_APP_VALID) + " 240 " + str(Device_Type_temp) + "\n") # make application valid
	thefile.close()	
	
def Create_Credential(file_path):	
	thislist = ["DEV_UN","DEV_PW","DEV_TYP","DEV_ID","DEV_RES1","DEV_RES2","MAST_MAC", "USER_MAC","USER_INFO","TEMP_MAC_RAND","TIME_VALID","CRED_TYPE"] #do not 
	n = 0
	for i in thislist:
		temp_data = raw_input("Enter " + i + ": ")
		thislist[n] = temp_data.replace(',','') # no comma alloud
		n = n+1
	str1 = ','.join(thislist) #comma is used to seprate cred
	print str1
	
	New_Hex_File_Path=os.path.splitext(file_path)[0]
	New_Hex_File_Path=New_Hex_File_Path + "_Usr"+ thislist[7] +".CRED" # 7 is user cred MAC
	thefile = open(New_Hex_File_Path, 'w')
	thefile.write(str1) # insert reflash command
	thefile.close()
	
def send_cred(cred_list,User_MAC_data):
	#thislist = ["saura","1234","1","12,34,5F,DF","DEV_RES1","DEV_RES2","44,55,77,8F", "2F,1F,2F,80","Employee","1F","10/10/2019,10/10/2020","NORMAL"]
	#mac_temp = "2F,1F,2F,80"
	#convert and send big frame
	
	cred_send =[0x51] # CRED command 
	cred_send.append(0x00)#rendom ENC keys
	cred_send.append(0x00)#rendom ENC keys
	cred_send.append(int(cred_list[9],16)) #RAND ID (key ?)
	
	temp_data = User_MAC_data.split(",")
	# perform conversion 
  
	for i in range(0, len(temp_data)): 
		temp_data[i] = (int(temp_data[i],16))
	
  
	cred_send.append(' '.join(str(e) for e in temp_data))			  #user mac

	temp_data = cred_list[3].split(",")
	for i in range(0, len(temp_data)): 
		temp_data[i] = (int(temp_data[i],16))
		
	cred_send.append(' '.join(str(e) for e in temp_data))			# device ID
 
	temp_data = cred_list[6].split(",")
	for i in range(0, len(temp_data)): 
		temp_data[i] = (int(temp_data[i],16))
		
	cred_send.append(' '.join(str(e) for e in temp_data))			# MASTER MAC
	
	temp_data = cred_list[7].split(",")
	for i in range(0, len(temp_data)): 
		temp_data[i] = (int(temp_data[i],16))
		
	cred_send.append(' '.join(str(e) for e in temp_data))			# USAR MAC

	str1 = ' '.join(str(e) for e in cred_send)
	print str1
	
def Write_Hex_to_bin_64(file_path,Device_Type_temp):
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
			length = int(line[1:3],16)/2			# data length in bytes# 1st two chrecter are length	 # 1:3 mease extrect 1 and 2nd charecter from line #int(line[1:2], 16)
			address = int(line[3:7],16) | (ext_add<<16)		# hex file address	# 3rd 4th 5th and 6th char are address 
			dat_type =	int(line[7:9],16)
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
					bl_frame_64_data = bl_frame_64_data + "00"*((FLASH_SECTOR_SIZE -((bl_frame_64_new_add_prv +length_prv) % FLASH_SECTOR_SIZE))*2)
			elif(ext_add!=0): # its eeprom data or config data
				if(bl_frame_64_new_add>=EEP_START_ADD):# its eeprom data 
					temp_data=list(split_by_n(data,4)) # eeprom data have some extra byte to be ignored in hex file
					temp_add=bl_frame_64_new_add
					for index in range(len(temp_data)):
						eep_frame.append(EEP_WR_CMD)
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
	temp_add = APP_START_ADD
	bl_data_64_farme = []
	New_Hex_File_Path=Hex_File_Path.replace('.','_Bin.')
	thefile = open(New_Hex_File_Path, 'w')
	print("Creating OTA file...\n")
	for index in range(len(list_b)):
		list_Temp = list_b[index]
		list_Temp = list(split_by_n(list_Temp,2))
		#print(list_Temp)
		
		bl_data_64_farme.append(FLSH_WR_CMD)
		bl_data_64_farme.append(temp_add & 0xFF)
		bl_data_64_farme.append((temp_add >> 8)&0xFF)
		for index in range(len(list_Temp)):
			checksum = checksum + int(list_Temp[index], 16) # flash mem checksum
			bl_data_64_farme.append(int(list_Temp[index], 16))
		#print(bl_data_64_farme)
		#print("\n")
		newFileByteArray = bytearray(bl_data_64_farme)		
		thefile.write(newFileByteArray)
		temp_add = temp_add + FLASH_SECTOR_SIZE;
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
	tmp_info = ser.read(RESPONCE_BYTE_LEN)
	#print tmp_info
	ser.reset_input_buffer()
	ser.reset_output_buffer()
	status = 0
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
	tmp_info = 0
	return status
def print_heading():
	print("\n -----------Boothost For PIC16F18313--------------\n")
	print("By Nandkumar G Dhavalikar (nandhavalikar@gmail.com)\n")
	print("K : Convert Hex to OTA\nF : Get New Fect Conf\nU : Get New User Cred\nR : Read Flash\nP : Program \nC : Clear Screen\nI : Ping\nV : Read Boot loader Version\nT : Catch BL\nH : Help \nQ : Exit \n")
def send_data(list_dat):
	ser.reset_input_buffer()
	ser.reset_output_buffer()
	for value in list_dat:
		ser.write(chr(value))
		time.sleep(0.001) # delay per charecter	

list_app_invalid = [EEP_WR_CMD, EEP_FDR_APP_VALID, 0xF0, NO_DEVICE] # [cmd add1 add0 data] write 00 at location 0x70FF of eeprom 
list_app_valid =   [EEP_WR_CMD, EEP_FDR_APP_VALID, 0xF0, DEMO] # [cmd add1 add0 data] write 0xAA at location 0x70FF of eeprom 
list_reset =	   [RESET_CMD]
list_ping =		   [PING_CMD]
list_Bl_ver =	   [EEP_RD_CMD, EEP_FECT_BL_VER, 0xF0] # read bl version no


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
		Device_Typ = raw_input("\nEnter Device	1:DEMO 2: Wall Switch ? : ") #read hex file path	
		Device_Typ = int(Device_Typ)
		if((Device_Typ > 0) and (Device_Typ < 3)):
		   print("\n----Log---\nHex File Entered : " + Hex_File_Path)
		   Write_Hex_to_String_64(Hex_File_Path,Device_Typ)
		else:
			print "Data Input Error"
	elif ((option == 'F') or (option == 'f')):
		Fect_File_Path = raw_input("\nEnter File path to store factory OTA file: ") #read hex file path	
		Device_Typ = raw_input("\nEnter Device	1:DEMO 2:Wall Switch ? : ") #read hex file path	
		Device_Typ = int(Device_Typ)
		if((Device_Typ > 0) and (Device_Typ < 3)):
		   Write_Fect_OTA_file(Fect_File_Path,Device_Typ)
		else:
			print "Data Input Error"
	elif ((option == 'U') or (option == 'u')):
		cred_File_Path = raw_input("\nEnter File path to store user credential: ") #read hex file path	
		Device_Typ = raw_input("\nEnter Device	1:DEMO 2:Wall Switch ? : ") #read hex file path	
		Device_Typ = int(Device_Typ)
		if((Device_Typ > 0) and (Device_Typ < 3)):
		   Create_Credential(cred_File_Path)
		else:
			print "Data Input Error"		
	elif ((option == 'P') or (option == 'p')):
		ser.open()
		time.sleep(1)
		temp = 0
		retry = 10
		while ((temp!=1) and (retry>0)):
			send_data(list_reset)
			time.sleep(BREAK)
			temp=reponce("RESET CMD ",RESET_CMD)
			retry = retry - 1;
		if(retry==0):
			print("\n No Response")
			ser.close()
			continue
		send_data(list_app_invalid)
		time.sleep(BREAK)
		temp=reponce("APP INVALID CMD ",EEP_WR_CMD)
		
		Hex_File_Path = raw_input("\nEnter complete OTA File path : ") #read hex file path	
		print("\n Hex File Entered : " + Hex_File_Path)
		Write_Hex_64(Hex_File_Path)
		
		#Flash_verify();
		
		send_data(list_app_valid)
		time.sleep(BREAK)
		temp=reponce("APP VALID CMD ",EEP_WR_CMD)
		
		send_data(list_reset)
		time.sleep(BREAK)
		temp=reponce("Programming ",RESET_CMD)
		
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
			temp=reponce("PING CMD ",PING_CMD)
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
		temp=reponce("BL VER CMD ",EEP_RD_CMD)
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
			temp=reponce("RESET CMD ",RESET_CMD)
			retry = retry - 1;
		if(retry==0):
			print("\n No Response")
			ser.close()
			continue
		send_data(list_app_invalid)
		time.sleep(BREAK)
		temp=reponce("APP INVALID CMD ",EEP_WR_CMD)
		if(temp==0):
			print("\n Power Cycle the controller while bootloader catch retry")
		ser.close()
	elif((option == 'H') or (option == 'h')):
		print("\nGenerated APP Loader hex File location is in hex file folder with name XXX.OTA")
		print("\nUART BAUD: 57600 , COM12 ")
	else:
		print("\n Unsupported or Unimplemented")