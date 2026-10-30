/** Safari may deny storage. Keep an explicit, exportable memory-only session. */
export function storage(getStorage, onFailure=()=>{}) {
 const memory=new Map();let failed=false;
 const warn=()=>{if(!failed){failed=true;onFailure();}};
 return {
  getItem(key){if(failed&&memory.has(key))return memory.get(key);try{const value=getStorage().getItem(key);if(value!==null)memory.set(key,value);return value;}catch{warn();return memory.get(key)??null;}},
  setItem(key,value){memory.set(key,value);try{getStorage().setItem(key,value);}catch{warn();}},
  removeItem(key){memory.set(key,null);try{getStorage().removeItem(key);}catch{warn();}}
 };
}
