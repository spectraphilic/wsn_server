<script>
    let error = false;
    let users = null;

    fetch('/demo/api/users')
        .then(function (response) {
            if (response.ok) {
                response.json().then(data => {
                    users = data;
                })
            }
            else {
                error = "Server Error";
            }
        })
        .catch(function (err) {
            error = err.message;
        });


    /*
    let result;

    function remove(user) {
        result = urql.mutationStore({
            client: $client,
            variables: {id: user.id},
            query: urql.gql`
                mutation deleteUser($id: ID!) {
                    deleteUser(filters: {id: {exact: $id}})
                    { id }
                }
            `,
        });
    }

    $: if ($result && $result.fetching == false) {
        if ($result.error) {
            console.log('ERROR', $result.error);
        } else {
            const id = $result.data.deleteUser[0].id;
            console.log('DELETED', id);
        }
    }
    */
</script>

<style>
    th, td {
        padding: 0 .5em;
    }
</style>

{#if error}
    {error}
{:else if users == null}
    <p>Loading...</p>
{:else}
    <table>
        <tr>
            <th>Id</th>
            <th>Username</th>
            <th>E-mail</th>
            <th>First name</th>
            <th>Last name</th>
            <th></th>
        </tr>
        {#each users as user}
        <tr>
            <td><a href="{user.id}/">{user.id}</a></td>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>{user.first_name}</td>
            <td>{user.last_name}</td>
            <td><button on:click|preventDefault={() => remove(user)}>Remove</button></td>
        </tr>
        {/each}
    </table>

    <p>
    <a href="create/">Add</a>
    </p>
{/if}
