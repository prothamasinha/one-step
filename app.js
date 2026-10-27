/* Vue 3, served locally. Every interaction and test uses fictional content. */
const { createApp } = Vue;
createApp({
  data() { return {
    screen: 'home', error: '', busy: false, simple: false, history: [], lastSession: null,
    sessionId: null, sessionStatus: null, elapsed: 0, pausedSeconds: 0, paused: false,
    startedAt: null, pauseStartedAt: null, pauseTotalMs: 0, timer: null,
    messageText: '', reply: '', responseMode: '', selectedHistory: null, savedMessages: []
  }; },
  computed: {
    phase() {
      if (this.paused) return 'paused';
      if (this.elapsed < 5 || this.elapsed >= 65) return '';
      return ((this.elapsed - 5) % 10) < 4 ? 'inhale' : 'exhale';
    },
    cueTitle() {
      if (this.paused) return 'Paused';
      if (this.elapsed < 5) return 'Follow the cue at your own pace';
      if (this.elapsed >= 65) return 'You can finish here';
      return this.phase === 'inhale' ? 'Breathe in' : 'Breathe out';
    },
    cueText() {
      if (this.paused) return 'Resume or leave whenever you choose.';
      if (this.elapsed < 5) return 'The practice will begin shortly.';
      if (this.elapsed >= 65) return 'No further steps are required.';
      return this.phase === 'inhale' ? '4 seconds' : '6 seconds';
    }
  },
  async mounted() {
    this.simple = localStorage.getItem('one-step-simple') === 'true';
    const interrupted = localStorage.getItem('one-step-active');
    if (interrupted) {
      try { await this.api('/api/sessions/' + Number(interrupted), 'PATCH', { status:'interrupted', actual_exercise_seconds:0, paused_seconds:0 }); }
      catch (err) { console.info('Could not mark previous session interrupted:', err); }
      localStorage.removeItem('one-step-active');
    }
    await this.loadHistory();
  },
  watch: { simple(val) { localStorage.setItem('one-step-simple', String(val)); } },
  methods: {
    async api(url, method='GET', body) {
      const response = await fetch(url, { method, headers: {'Content-Type':'application/json'}, body:body?JSON.stringify(body):undefined });
      if (!response.ok) throw new Error('Request failed (' + response.status + ').');
      return response.json();
    },
    async loadHistory() {
      try { this.history = await this.api('/api/sessions'); this.lastSession = this.history[0] || null; }
      catch (e) { this.error = 'Saved history is temporarily unavailable. Crisis support remains available.'; }
    },
    async startExercise() {
      this.busy = true; this.error='';
      try {
        const session = await this.api('/api/sessions', 'POST', {skill_type:'breathing'});
        this.sessionId=session.id; localStorage.setItem('one-step-active', String(session.id));
        this.sessionStatus=null;this.elapsed=0;this.pausedSeconds=0;this.pauseTotalMs=0;this.paused=false;this.reply='';this.messageText='';
        this.startedAt=performance.now();this.screen='exercise';
        this.timer = setInterval(this.tick, 100);
      } catch(e) { this.error='Could not start the exercise. You can retry or open Crisis support.'; }
      finally { this.busy=false; }
    },
    tick() {
      if (!this.paused && this.startedAt!==null) {
        this.elapsed = Math.max(0, (performance.now() - this.startedAt - this.pauseTotalMs)/1000);
        if (this.elapsed >= 70) this.endExercise('completed');
      }
    },
    togglePause() {
      if (this.paused) {
        const pausedMs=performance.now()-this.pauseStartedAt;
        this.pauseTotalMs+=pausedMs; this.pausedSeconds=this.pauseTotalMs/1000;this.paused=false;this.pauseStartedAt=null;
      } else { this.tick(); this.paused=true;this.pauseStartedAt=performance.now(); }
    },
    async endExercise(status) {
      if (this.screen!=='exercise' || this.busy) return;
      // Freeze the measurement before a network request; that request ends after the final skill cue.
      if (!this.paused) this.tickWithoutFinishing();
      else this.pausedSeconds=(this.pauseTotalMs + performance.now()-this.pauseStartedAt)/1000;
      clearInterval(this.timer);this.timer=null;this.busy=true;this.sessionStatus=status;
      if(status==='completed') this.elapsed=Math.max(70,this.elapsed);
      localStorage.removeItem('one-step-active');
      try { await this.api('/api/sessions/'+this.sessionId, 'PATCH', { status,actual_exercise_seconds:this.elapsed,paused_seconds:this.pausedSeconds }); }
      catch(e) { this.error='The session could not be saved. You may still leave or open Crisis support.'; }
      this.screen='done'; this.busy=false;
    },
    tickWithoutFinishing() { this.elapsed=Math.max(0,(performance.now()-this.startedAt-this.pauseTotalMs)/1000); },
    async sendChat() {
      this.busy=true;this.error='';
      try { const out=await this.api('/api/chat', 'POST',{session_id:this.sessionId,text:this.messageText.trim()});this.reply=out.reply;this.responseMode=out.response_mode;this.messageText=''; }
      catch(e) { this.error='Chat is unavailable. You can return home or open Crisis support.'; }
      finally {this.busy=false;}
    },
    async openHistory() { await this.loadHistory(); this.selectedHistory=null;this.savedMessages=[];this.screen='history'; },
    async loadMessages(id) { this.selectedHistory=id;try{this.savedMessages=await this.api('/api/messages?session_id='+id);}catch(e){this.error='Could not load messages.';} },
    async goHome() { this.screen='home';await this.loadHistory(); }
  }
}).mount('#app');
