import UsersCreate from './demo/UsersCreate.svelte';
import UsersList from './demo/UsersList.svelte';
import UsersUpdate from './demo/UsersUpdate.svelte';

// XXX Hack to force vite build to output components
console.debug(UsersCreate, UsersList, UsersUpdate);

export { UsersCreate, UsersList, UsersUpdate };
