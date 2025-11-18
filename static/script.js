console.log("Now active");

const chatEl = document.getElementById('chat')
const inputForm = document.getElementById('inputForm')
const messageInput = document.getElementById('messageInput')
const sendBtn = document.getElementById('sendBtn')
const newConvBtn = document.getElementById('newConv')

function createMessageEl(role, text, isLoader=false){
	const el = document.createElement('div')
	el.className = 'message ' + (role === 'user' ? 'user' : 'assistant')
	if(isLoader){
		el.innerHTML = `<div class="loader dots"><span></span><span></span><span></span></div>`
	} else {
		el.textContent = text
	}
	return el
}

function scrollToBottom(){
	chatEl.scrollTop = chatEl.scrollHeight
}

async function loadConversation(){
	try{
		const res = await fetch('/api/conversations')
		if(!res.ok) throw new Error('Failed to load')
		const data = await res.json()
		chatEl.innerHTML = ''
		(data.messages || []).forEach(m => {
			const el = createMessageEl(m.role, m.content)
			chatEl.appendChild(el)
		})
		scrollToBottom()
	}catch(err){
		console.error(err)
	}
}

async function sendMessage(){
	const text = messageInput.value.trim()
	if(!text) return

	// show user message immediately
	const userEl = createMessageEl('user', text)
	chatEl.appendChild(userEl)
	scrollToBottom()
	messageInput.value = ''

	// show loader
	const loaderEl = createMessageEl('assistant', '', true)
	chatEl.appendChild(loaderEl)
	scrollToBottom()

	try{
		const res = await fetch('/api/chat', {
			method: 'POST',
			headers: {'Content-Type':'application/json'},
			body: JSON.stringify({message: text})
		})
		if(!res.ok) throw new Error('Chat failed')
		const data = await res.json()

		// replace loader with assistant message
		const assistantText = data.reply || (data.messages && data.messages.slice(-1)[0].content) || 'No reply'
		const assistantEl = createMessageEl('assistant', assistantText)
		chatEl.replaceChild(assistantEl, loaderEl)
		scrollToBottom()
	}catch(err){
		console.error(err)
		const errEl = createMessageEl('assistant', 'Error: could not get reply')
		chatEl.replaceChild(errEl, loaderEl)
		scrollToBottom()
	}
}

inputForm.addEventListener('submit', (e)=>{ e.preventDefault(); sendMessage() })
sendBtn.addEventListener('click', sendMessage)
newConvBtn && newConvBtn.addEventListener('click', async ()=>{
	await fetch('/api/conversations/clear', {method:'POST'})
	chatEl.innerHTML = ''
})

// load initial conversation
loadConversation()