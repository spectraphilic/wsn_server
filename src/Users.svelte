<script>
    import { initClient } from '@urql/svelte';
    import { operationStore, query } from '@urql/svelte';

    export let extra = 0;

    initClient({
        url: 'http://localhost:8000/graphql',
    });

    const users = operationStore(`
        query {
            users {
                id
                username
                email
                firstName
                lastName
            }
        }
    `);

    query(users);
</script>

<style>
    div {
        margin: auto;
        width: fit-content;
    }
    button {
        float: right;
    }
</style>

{#if $users.fetching}
    <p>Loading...</p>
{:else if $users.error}
    <p>Oh no... {$users.error.message}</p>
{:else}
<div>
    <table>
        <tr>
            <th>Id</th>
            <th>Username</th>
            <th>E-mail</th>
            <th>First name</th>
            <th>Last name</th>
        </tr>
        {#each $users.data.users as user}
        <tr>
            <td>{user.id}</td>
            <td><input type="text" value={user.username}></td>
            <td><input type="text" value={user.email}></td>
            <td><input type="text" value={user.firstName}></td>
            <td><input type="text" value={user.lastName}></td>
        </tr>
        {/each}
        {#if extra}
        <tr>
            <td></td>
            <td><input type="text"></td>
            <td><input type="text"></td>
            <td><input type="text"></td>
            <td><input type="text"></td>
        </tr>
        {/if}
    </table>
    <button>Save</button>
</div>
{/if}
