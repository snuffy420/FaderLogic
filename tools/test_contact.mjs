// Test the actual contact-page script in a simulated DOM. No network requests.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../docs/contact.html',import.meta.url),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
assert.match(html,/action="https:\/\/formspree.io\/f\/myeekrpy"/);
assert.match(html,/type="email"[^>]*required/);assert.match(html,/name="_gotcha"/);
function fixture(mode='success'){
 const ids=['contactForm','submitBtn','buttonText','status','message','count'];
 const elements=Object.fromEntries(ids.map(id=>[id,{value:'',textContent:'',dataset:{},disabled:false,events:{},validity:'',addEventListener(name,fn){this.events[name]=fn;},removeAttribute(){this.dataset={};},setCustomValidity(text){this.validity=text;}}]));
 elements.contactForm.action='https://formspree.io/f/myeekrpy';
 elements.contactForm.reportValidity=()=>!elements.message.validity;
 elements.contactForm.reset=()=>{elements.message.value='';};
 let requests=0,resolvePending;
 const context={document:{getElementById:id=>elements[id]},AbortController,setTimeout:()=>1,clearTimeout:()=>{},FormData:class{},fetch:async(url,options)=>{
  requests++;assert.equal(url,elements.contactForm.action);assert.equal(options.method,'POST');assert.equal(options.headers.Accept,'application/json');
  if(mode==='pending')await new Promise(resolve=>{resolvePending=resolve;});
  if(mode==='offline')throw new Error('Failed to fetch');
  if(mode==='timeout'){const error=new Error('Aborted');error.name='AbortError';throw error;}
  return mode==='invalid'?{ok:false,json:async()=>({errors:[{message:'Please check your email.'}]})}:{ok:true};
 }};
 vm.runInNewContext(script,context);
 const submit=()=>elements.contactForm.events.submit({preventDefault(){}});
 return {elements,submit,get requests(){return requests;},finish:()=>resolvePending()};
}
for(const mode of ['success','invalid','offline','timeout']){
 const f=fixture(mode);f.elements.message.value='A local-only test message.';
 await f.submit();assert.equal(f.requests,1);assert.equal(f.elements.submitBtn.disabled,false);assert.equal(f.elements.buttonText.textContent,'Send message');
 if(mode==='success'){assert.equal(f.elements.status.dataset.state,'success');assert.equal(f.elements.message.value,'');}
 else{assert.equal(f.elements.status.dataset.state,'error');assert.equal(f.elements.message.value,'A local-only test message.');}
}
const empty=fixture();empty.elements.message.value='   ';await empty.submit();assert.equal(empty.requests,0);
const counter=fixture();counter.elements.message.value='Hello';counter.elements.message.events.input();assert.equal(counter.elements.count.textContent,'5');
const pending=fixture('pending');pending.elements.message.value='Local only';const first=pending.submit();await pending.submit();assert.equal(pending.requests,1);assert.equal(pending.elements.submitBtn.disabled,true);pending.finish();await first;
console.log('PASS: actual form script — success, service errors, offline, timeout, whitespace validation, character count, duplicate-submit protection; no network/message sent');
