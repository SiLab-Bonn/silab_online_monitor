To start the online monitor example with the pyBAR plugins do the following:

1. Change the data_file parameter in the configuration.yaml to point to the pybar_data.h5 in this folder.
2. Open a console
3. Type:
   start_online_monitor EXAMPLE_PATH/configuration.yaml
  
   where EXAMPLE_PATH is the path of this example.
  
 This will start the pyBAR simulation producer replaying real data, pyBAR converter converting the raw data on the fly and the pyBAR receiver showing some plots.