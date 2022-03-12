<script>
    import * as urql from '@urql/svelte';

    urql.initClient({
        url: '/demo/graphql/',
    });

    const users = urql.operationStore(`
        query {
            users { id username email firstName lastName }
        }
    `);

    const deleteUser = urql.mutation({query: `
        mutation deleteUser($id: ID!) {
            deleteUser(filters: {id: {exact: $id}})
            { id }
        }
    `});

    urql.query(users);

    function remove(user) {
        deleteUser({id: user.id}).then(result => {
            if (result.error) {
                console.log(result.error);
            } else {
                //data = result.data.updateUser[0];
            }
        });
    }
</script>

<style>
    th, td {
        padding: 0 .5em;
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
            <th></th>
        </tr>
        {#each $users.data.users as user}
        <tr>
            <td><a href="{user.id}/">{user.id}</a></td>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>{user.firstName}</td>
            <td>{user.lastName}</td>
            <td><a href="" on:click|preventDefault={() => remove(user)}>Remove</a></td>
        </tr>
        {/each}
    </table>

    <p>
    <a href="create/">Add</a>
    </p>
</div>
{/if}
