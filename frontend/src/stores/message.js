import { defineStore } from 'pinia';

export const useMessageStore = defineStore('messageList', {
  state: () => ({
    errorMessages: []
  }),
  getters: {
    allMessages(state) {
      return state.errorMessages;
    }
  },
  actions: {
    removeMessage() {
      return this.errorMessages.shift;
    },
    addMessage(message) {
      this.errorMessages.push(message)
    }
  }

});
