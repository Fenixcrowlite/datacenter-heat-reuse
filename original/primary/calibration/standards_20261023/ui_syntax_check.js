
const $=id=>document.getElementById(id), keys=['L','W','D','t0','ts','toff','qh','ql','cop','sT','ap','it','ut','pue','rec','pE','pG','etaG'];
let latest={};
function num(id){return Number($(id).value)}
function fmt(x,n=2){return Number.isFinite(x)?x.toLocaleString('ru-RU',{maximumFractionDigits:n}):'нет'}
function addMetric(k,v,unit,n=2){return '<div class="card"><small>'+k+'</small><strong class="result">'+fmt(v,n)+' '+unit+'</strong></div>'}
function update(){
 let x=Object.fromEntries(keys.map(k=>[k,num(k)]));let warnings=[];
 if(x.L<=0||x.W<=0||x.D<=0||x.qh<=0||x.cop<=1||x.pue<1||x.ut<0||x.ut>1||x.rec<0||x.rec>1||x.ql<0||x.ts<x.t0||x.pE<0||x.pG<0||x.etaG<=0||x.etaG>1){$('results').innerHTML='Проверьте диапазоны ввода';$('checks').innerHTML='';return}
 const V=x.L*x.W*x.D,E=997*V*4182*(x.ts-x.t0)/3.6e9;
 const loss=x.ql*(x.L*x.W/312.5),net=x.qh-loss,h=net>0?E*1000/net:NaN,IT=x.it*x.ut;
 const edc=IT*8760*x.pue,esurvey=IT*8760*1.52,src=IT*x.rec;
 const poolYear=loss*8.76+E,hpsource=poolYear*(1-1/x.cop),erf=Math.min(hpsource,src*8760)/edc;
 latest={date:'2026-10-23',assumptions:x,outputs:{V_m3:V,Eheat_MWh:E,screening_heatup_h:h,IT_MW:IT,EDC_annual_MWh:edc,EDC_market_reference_MWh:esurvey,pool_year_screening_MWh:poolYear,HP_source_screening_MWh:hpsource,ERF_screening:erf},classification:'ALL CALCULATED OUTPUTS ARE SCENARIO SCREENING, NOT MEASUREMENTS'};
 $('results').innerHTML=[
 addMetric('Объём воды',V,'м³'),addMetric('Идеальная энергия нагрева',E,'МВт·ч',3),addMetric('Потери при выбранной площади, сценарий',loss,'кВт',2),
 addMetric('Нагрев с постоянными потерями',h,'ч'),addMetric('Электроэнергия ТЧ на начальный нагрев',E/x.cop,'МВт·ч',3),
 addMetric('Мощность IT по загрузке',IT,'МВт'),addMetric('Мощность возможной рекуперации IT',src,'МВт'),
 addMetric('Энергия ЦОД за год при выбранном PUE',edc,'МВт·ч',0),
 addMetric('При отраслевом PUE 1,52, та же IT энергия',esurvey,'МВт·ч',0),
 addMetric('Отличие ЦОД от ориентира 2026',edc-esurvey,'МВт·ч',0),
 addMetric('Годовой нагрев бассейна, упрощённо',poolYear,'МВт·ч'),
 addMetric('Электроэнергия ТЧ за год, сценарий',poolYear/x.cop,'МВт·ч'),
 addMetric('OPEX ТЧ за год, сценарий',poolYear/x.cop*x.pE,'€',0),
 addMetric('OPEX газового аналога, сценарий',poolYear/x.etaG*x.pG,'€',0),
 addMetric('Разница OPEX, без CAPEX и насосов',poolYear*(x.pG/x.etaG-x.pE/x.cop),'€',0),
 addMetric('ERF для одного бассейна, приближение',erf*100,'%',3)
 ].join('');
 if(x.toff>28)warnings.push('Порог выключения '+fmt(x.toff)+' °C выше опубликованного предела 28 °C: для реального объекта это недопустимый проектный режим без юридического пересмотра.');
 if(x.ts>=28)warnings.push('Заданная температура находится на пределе 28 °C: нет запаса на датчик и инерцию.');
 if(net<=0)warnings.push('Мощности нагрева не хватает даже на принятые постоянные потери.');
 if(x.L*x.W!==312.5)warnings.push('Потери масштабированы по площади воды относительно 312,5 м². Это приближение, для иной геометрии нужен полный теплобаланс.');
 if(x.sT<x.ts+x.ap)warnings.push('Прямой теплообменник не проходит простое условие температурного напора; нужна HP/иная температура.');
 warnings.push('Потери '+fmt(x.ql)+' кВт, загрузка IT, доля рекуперации и COP сейчас сценарные, а не измеренные.');
 warnings.push('ERF рассчитан ориентировочно. Для отчётности EU нужны годовые измерения энергии на границе дата-центра.');
 $('checks').innerHTML=warnings.map((w,i)=>'<div class="'+(i<2&&w.includes('выше')?'warning':'good')+'">'+w+'</div>').join('');
}
function preset(b){$('L').value='25';$('W').value=b?'20':'12.5';$('D').value=b?'2':'1.6';update()}
function exportJSON(){
 const blob=new Blob([JSON.stringify(latest,null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='dc_pool_parameter_scenario.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
keys.forEach(k=>$(k).addEventListener('input',update)); update();

