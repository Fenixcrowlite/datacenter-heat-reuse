
const config=[['IT','IT нагрузка, МВт',10,0.1,1],['N','Всего модулей, включая один резервный',7,2,1],['unit','Паспортная мощность модуля, МВт',2,0.1,.1],['derate','Снижение мощности при жаре, %',10,0,1],['delay','Время выхода резерва, с',30,0,10],['delta','Допустимый нагрев буфера, K',5,.1,.5],['dt','ΔT через охлаждение, K',5,.1,.5],['velocity','Допустимая скорость воды, м/с',2,.1,.5],['buffer','Фактический буфер, м³',10,0,1],['ups','Допустимое время питания насосов от UPS, с',300,0,10]];
const inp=document.getElementById('inputs'),out=document.getElementById('results');const vals={};
config.forEach(([id,title,def,min,step])=>{inp.insertAdjacentHTML('beforeend','<div class="card"><label>'+title+'</label><input id="'+id+'" type="number" min="'+min+'" step="'+step+'" value="'+def+'"></div>');document.getElementById(id).addEventListener('input',update)});
const nf=(x,d=2)=>Number.isFinite(x)?x.toLocaleString('ru-RU',{maximumFractionDigits:d}):'—';
function update(){
const v={};config.forEach(([id])=>v[id]=Number(document.getElementById(id).value));
if(v.IT<=0||v.N<2||v.unit<=0||v.derate<0||v.derate>=100||v.delta<=0||v.dt<=0||v.velocity<=0||v.delay<0){out.innerHTML='';document.getElementById('alert').textContent='Недопустимое значение';return;}
const useful=v.unit*(1-v.derate/100),normal=(v.N-1)*useful,during=Math.max(0,v.N-2)*useful,restored=normal;
const deficiency=Math.max(0,v.IT-during),persistent=Math.max(0,v.IT-restored),thermal=deficiency*v.delay*1e6/(997*4182*v.delta);
const flow=v.IT*1e6*3600/(997*4182*v.dt),diameter=Math.sqrt(4*flow/(3600*Math.PI*v.velocity))*1000;
const metrics=[['Рабочая мощность до отказа',normal,'МВт'],['После отказа до включения резерва',during,'МВт'],['После запуска резерва',restored,'МВт'],['Дефицит до запуска',deficiency,'МВт'],['Требуемый буфер (идеальный минимум)',thermal,'м³'],['Расход IT воды',flow,'м³/ч'],['Внутренний диаметр одного трубопровода',diameter,'мм'],['Непокрытый дефицит после запуска',persistent,'МВт']];
out.innerHTML=metrics.map(([a,b,c])=>'<div class="card"><small>'+a+'</small><b class="n">'+nf(b)+' '+c+'</b></div>').join('');
let messages=[];
if(persistent>1e-8)messages.push('Недостаточная охлаждающая мощность после восстановления N+1: буфер лишь откладывает перегрев.');
if(v.buffer+1e-8<thermal)messages.push('Доступный объём буфера меньше идеального минимума при выбранном времени перехода.');
if(v.ups<v.delay)messages.push('UPS насосов короче времени переключения: сохранение расхода не обеспечено.');
if(!messages.length)messages=['Проверка выбранных чисел пройдена. Это НЕ означает подтверждённую безопасность объекта: нужна заводская кривая мощности при максимальной наружной температуре и фактическая гидравлика.'];
const box=document.getElementById('alert');box.className=(persistent<1e-8&&v.buffer>=thermal&&v.ups>=v.delay?'good':'');box.textContent=messages.join(' ');
vals.payload={input:v,output:{cooling_normal_MW:normal,cooling_during_fault_MW:during,cooling_after_spare_MW:restored,transient_deficit_MW:deficiency,persistent_deficit_MW:persistent,minimum_buffer_m3:thermal,water_flow_m3h:flow,pipe_ID_mm:diameter},disclaimer:'Ideal thermal screening only. Real equipment performance, failure detection, UPS and piping to be certified.'};
}
function reset(){config.forEach(([id,title,def])=>document.getElementById(id).value=def);update()}
function save(){let blob=new Blob([JSON.stringify(vals.payload,null,2)],{type:'application/json'});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='cooling_Nplus1_parameters.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),800)}
update();
