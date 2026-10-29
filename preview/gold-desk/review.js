(()=>{
 const frame=document.getElementById('design'),stage=document.getElementById('stage');
 const buttons=[...document.querySelectorAll('[data-width]')];let selected='auto';
 function size(){
  if(!frame.contentDocument?.body)return;
  const available=stage.clientWidth,width=selected==='auto'?available:Number(selected);
  const scale=Math.min(1,available/width);
  frame.style.width=width+'px';frame.style.height='100px';
  const height=frame.contentDocument.documentElement.scrollHeight;
  frame.style.height=height+'px';frame.style.transform=`scale(${scale})`;
  stage.style.height=Math.ceil(height*scale)+'px';
  document.getElementById('layout').textContent=(selected==='auto'?'Responsive layout at your screen width':`Layout at ${width} px`)+(scale<1?` · scaled to ${Math.round(scale*100)}% to fit. Open full-screen for readable device-sized text.`:'.');
 }
 buttons.forEach(button=>button.onclick=()=>{selected=button.dataset.width;buttons.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));size();});
 frame.addEventListener('load',()=>{size();new MutationObserver(size).observe(frame.contentDocument.body,{subtree:true,childList:true,characterData:true});frame.contentDocument.fonts.ready.then(size);});
 window.addEventListener('resize',size);
})();
