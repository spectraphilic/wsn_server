<script>
    import * as urql from '@urql/svelte';

    let id;
    let username = '';
    let email = '';
    let firstName = '';
    let lastName = '';

    urql.initClient({
        url: '/graphql',
    });

    const mutation = urql.mutation({query: `
        mutation createUser(
            $username: String!,
            $email: String,
            $firstName: String,
            $lastName: String)
        {
            createUser(
                data: {
                    username: $username,
                    email: $email,
                    firstName: $firstName,
                    lastName: $lastName
                },
            ) {
                id
                username
                email
                firstName
                lastName
            }
        }
    `});

    function update(ev) {
        ev.preventDefault();
        const input = {id, username, email, firstName, lastName};
        mutation(input).then(result => {
            if (result.error) {
                console.log(result.error);
            } else {
                window.location.href = '..';
            }
        });
    }
</script>

<style>
    form div {
        margin-bottom: 1em;
    }
</style>

<form on:submit={update}>
    <div>
        <label>
            Username<br>
            <input type="text" bind:value={username}>
        </label>
    </div>

    <div>
        <label>
            E-mail<br>
            <input type="text" bind:value={email}>
        </label>
    </div>

    <div>
        <label>
            First name<br>
            <input type="text" bind:value={firstName}>
        </label>
    </div>

    <div>
        <label>
            Last name<br>
            <input type="text" bind:value={lastName}>
        </label>
    </div>

    <div>
        <button type="submit">Create</button>
    </div>
</form>
