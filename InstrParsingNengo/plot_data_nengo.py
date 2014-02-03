import os
if os.name == "java":
    print "Run this in the regular puthon console"

else:
    import sys
    sys.path.append("C:\\Users\\xchoo\\GitHub\\nengo_1.4\\simulator-ui\\python")
    # sys.path.append("D:\\fchoo\\Documents\\GitHub\\nengo_1.4\\simulator-ui\\python")
    # sys.path.append("F:\\xchoo\\Documents\\Dropbox\\Thesis - PhD\\Code\\Python\\DelayTest\\")
    # sys.path.append("D:\\fchoo\\Documents\\My Dropbox\\Thesis - PhD\\Code\\Python\\DelayTest\\")
    # sys.path.append("D:\\Users\\xchoo\\Dropbox\\Thesis - PhD\\Code\\Python\\DelayTest\\")

    import stats
    import stats.plot

    data_dir = "E:\\Data\\Cogsci2014"
    #data_file = "Test 2014-02-01 19-01-15-122999-20140201-190848"
    #data_file = "Test 2014-02-01 20-14-57-641000-20140201-202232"
    #data_file = "Test 2014-02-01 20-39-24-973000-20140201-204649"
    #data_file = "Test 2014-02-01 21-48-18-201999-20140201-215935"
    #data_file = "Test 2014-02-01 22-26-41-086999-20140201-223750"
    #data_file = "Test 2014-02-02 03-15-16-509000-20140202-032649"
    #data_file = "Test 2014-02-02 05-46-31-650000-20140202-055748"
    data_file = "Test 2014-02-02 07-38-37-342999-20140202-075455"
    data = stats.Reader("%s.csv" % data_file, data_dir)

    plot = stats.plot.Time(data['time'], width=9, height=6, ylabel_rotation = 'horizontal', border_left=1)
    plot.add("Vision", data.get("vis.vis_out_vocab", keys=["square", "circle"]), num_yticks=0)
    plot.add_spikes('Vision\n(Spikes)', data['vis.VISION_spikes'], cluster = True, sample = 8000, sample_by_variance = 50, yticks = [])
    plot.add("Auditory", data.get("aud.aud_out_vocab", keys=["one", "two"]), num_yticks=0)
    plot.add_spikes('Auditory\n(Spikes)', data['aud.AUDITORY_spikes'], cluster = True, sample = 8000, sample_by_variance = 50, yticks = [])
    plot.add("Sensor\nVerb", data.get("instr.SENSOR IN.X_vocab", keys=["hear", "see","square", "circle", "one", "two"]), num_yticks=0)
    plot.add("Sensor\nNoun", data.get("instr.S_DATA IN.X_vocab", keys=["hear", "see","square", "circle", "one", "two"]), num_yticks=0)
    # plot.add("Rule\nPosition", data.get("instr.CConv Pos Out.X_vocab", keys=["P0", "P1", "P2", "P3", "P4"]), num_yticks=0)
    plot.add("Rule\nPosition", data.get("instr.CleanupPos.X_vocab", keys=["P0", "P1", "P2", "P3", "P4"]), num_yticks=0)
    plot.add("Action\nVerb", data.get("instr.CleanupAction.X_vocab", keys=["write", "press", "num1", "num2","button1", "button2"]), num_yticks=0)
    plot.add("Action\nNoun", data.get("instr.CleanupActionData.X_vocab", keys=["write", "press", "num1", "num2","button1", "button2"]), num_yticks=0)
    plot.add("Motor", data.get("motor.Motor Out.X_vocab", keys=["write*num1", "write*num2", "press*button1", "press*button2"]), num_yticks=0)
    plot.add_spikes('Motor\n(Spikes)', data['motor.Motor Out_spikes'], cluster = True, sample = 8000, sample_by_variance = 50, yticks = [])
    plot.save('test.png')
    plot.show()