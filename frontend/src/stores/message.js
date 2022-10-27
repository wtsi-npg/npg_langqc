import { defineStore } from 'pinia';

const useMessageStore = defineStore('messageList', {
  state: () => ({
    errorMessages: []
  }),
  getters: {

  },
  actions: {
    removeMessage() {
      this.errorMessages.shift
    },
    addMessage(message) {
      this.errorMessages.push(message)
    }
  }

});

export default useMessageStore;
