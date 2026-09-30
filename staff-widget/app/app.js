"use strict";
// This widget relies on CRM authentication. No token, API key or password in JS.
const actions = {
  attendance:{fn:"sms_record_attendance",fields:[["enrollment_id","Enrollment record ID"],["date_text","Attendance date","date"],["attendance_status","Status","select",["Present","Absent","Late","Excused"]]]},
  result:{fn:"sms_record_result",fields:[["enrollment_id","Enrollment record ID"],["paper_id","Exam paper record ID"],["marks_text","Marks","number"],["was_absent","Student was absent","checkbox"]]},
  invoice:{fn:"sms_create_invoice",fields:[["enrollment_id","Enrollment record ID"],["invoice_reference","Invoice reference"],["amount_text","Total fee in INR","number"],["due_date","Due date","date"]]},
  payment:{fn:"sms_record_payment",fields:[["invoice_id","Fee invoice record ID"],["amount_text","Amount received in INR","number"],["payment_reference","Unique payment reference"],["date_text","Payment date","date"]]},
  admission:{fn:"sms_confirm_admission",fields:[["lead_id","Approved lead record ID"]]},
  promotion:{fn:"sms_promote",fields:[["previous_enrollment_id","Previous enrollment record ID"],["new_section_id","New academic year section ID"]]}
};
let context = {};
let ready = false;
const action = document.querySelector("#action");
const form = document.querySelector("#operation");
const fields = document.querySelector("#fields");
const output = document.querySelector("#out");
const button = document.querySelector("#save");
function render(){
  fields.replaceChildren();
  for(const [name,title,type="text",choices] of actions[action.value].fields){
    const label=document.createElement("label");label.htmlFor=name;label.textContent=title;
    const input=document.createElement(type==="select"?"select":"input");
    input.id=name;input.name=name;
    if(type==="select") for(const value of choices){const opt=document.createElement("option");opt.value=value;opt.textContent=value;input.append(opt);}
    else input.type=type;
    input.required=type!=="checkbox";
    if(type==="number"){input.min="0";input.max="9999999999.99";input.step="0.01";}
    if(name.endsWith("_id")){input.inputMode="numeric";input.pattern="[0-9]{1,30}";}
    const recordId=Array.isArray(context.EntityId)?context.EntityId[0]:context.EntityId;
    if(recordId && ((context.Entity==="Enrollments" && ["enrollment_id","previous_enrollment_id"].includes(name)) || (context.Entity==="Fee_Invoices" && name==="invoice_id") || (context.Entity==="Leads" && name==="lead_id"))) input.value=String(recordId);
    fields.append(label,input);
  }
}
action.addEventListener("change",render);
form.addEventListener("submit",async event=>{
  event.preventDefault();if(!ready || !form.reportValidity())return;
  const config=actions[action.value];
  const args={};
  for(const [name,,type] of config.fields){const el=form.elements.namedItem(name);args[name]=type==="checkbox"?el.checked:el.value.trim();}
  button.disabled=true;output.textContent="Saving…";
  try{
    const response=await ZOHO.CRM.FUNCTIONS.execute(config.fn,{arguments:JSON.stringify(args)});
    if(response.code!=="success" || !response.details || response.details.output==null)throw new Error("CRM did not return a function result. Check the record before retrying.");
    const result=typeof response.details.output==="string"?JSON.parse(response.details.output):response.details.output;
    if(!result.ok)throw new Error(result.error || "Validation failed");
    output.textContent=(result.replayed?"Already saved. Duplicate submission ignored.":"Saved successfully.")+(result.id?" Record ID: "+result.id:"")+(result.student_id?" Student record ID: "+result.student_id:"")+(result.summary_updated===false?" Summary refresh needs administrator attention; the record was saved.":"");
  }catch(error){output.textContent="Could not complete: "+error.message;}
  finally{button.disabled=false;}
});
render();
if(typeof ZOHO!=="undefined"){
  ZOHO.embeddedApp.on("PageLoad",data=>{context=data||{};render();});
  ZOHO.embeddedApp.init().then(()=>{ready=true;button.disabled=false;document.querySelector("#connection").textContent="Connected to Zoho CRM. Use an authorized school staff account.";}).catch(()=>{document.querySelector("#connection").textContent="Open this widget inside Zoho CRM to continue.";});
}else document.querySelector("#connection").textContent="Open this widget inside Zoho CRM. It does not write records when opened as a local file.";
