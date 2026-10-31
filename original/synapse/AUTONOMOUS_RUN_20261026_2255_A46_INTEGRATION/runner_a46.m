try
  run('C:/Users/Lysda/Desktop/SynapseControlCenter/recovery/AUTONOMOUS_RUN_20261026_2255_A46_INTEGRATION/build_a46.m');
catch ME
  disp(getReport(ME,'extended'));
  exit(2);
end
exit(0);
