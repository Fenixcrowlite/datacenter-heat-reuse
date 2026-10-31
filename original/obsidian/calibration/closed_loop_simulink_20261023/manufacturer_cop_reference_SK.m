function [cop,status]=manufacturer_cop_reference_SK(sourceOutlet_C,sinkOutlet_C,rootDir)
% Manufacturer/Eurovent data only within observed points for EXACT source W10-7.
% NO extrapolation to model DC source 25/35 C or district heat at 70C.
if nargin<3,rootDir=fileparts(mfilename('fullpath'));end
assert(isfinite(sourceOutlet_C)&&isfinite(sinkOutlet_C));
points=readtable(fullfile(rootDir,'manufacturer_certified_points_carrier.csv'));
cop=NaN;
status="UNSUPPORTED_UNCERTIFIED_CONDITION";
if abs(sourceOutlet_C-7)>1e-8
 return
end
if sinkOutlet_C<min(points.sink_out_C) || sinkOutlet_C>max(points.sink_out_C)
 return
end
cop=interp1(points.sink_out_C,points.COP,sinkOutlet_C,'linear');
if any(abs(sinkOutlet_C-points.sink_out_C)<1e-8)
 status="EUROVENT_CERTIFIED_POINT";
else
 status="INTERPOLATED_NONCERTIFIED_BETWEEN_POINTS";
end
end
