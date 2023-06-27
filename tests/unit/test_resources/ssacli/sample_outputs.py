CTRL_ALL_SHOW = """

Smart Array P222 in Slot 2                (sn: PDSXH0BRH6G0QU)
Smart HBA P222 in Slot 3                (sn: PDSXH0BRH6G0QU)

"""
CTRL_SHOW_STATUS = """

Smart Array P222 in Slot 2
   Random bad output line
   Controller Status: OK
   Cache Status: OK
   Battery/Capacitor Status: OK


"""
CTRL_LD_ALL_SHOW_STATUS = """

   logicaldrive 1 (931.48 GB, RAID 1): OK

"""
CTRL_PD_ALL_SHOW_STATUS = """

   physicaldrive 2I:0:1 (port 2I:box 0:bay 1, 1 TB): OK
   physicaldrive 2I:0:2 (port 2I:box 0:bay 2, 1 TB): OK

"""

CTRL_LD_ALL_SHOW_STATUS_ABSENT = """

Error: The specified controller does not have any logical drive.

"""

CTRL_PD_ALL_SHOW_STATUS_ABSENT = """

Error: The specified controller does not have any physical drive.

"""
